"""Tests pour les webhooks PayPal"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from shop.models import Order, Payment, WebhookEvent, Book, Category
from shop.webhooks import verify_paypal_signature, paypal_webhook
from shop.webhook_handlers import (
    extract_order_id_from_paypal_payload,
    handle_checkout_order_completed,
    handle_payment_capture_refunded,
)

User = get_user_model()


class WebhookSignatureTests(TestCase):
    """Tests pour la validation de signature"""

    def setUp(self):
        self.client = Client()

    @patch("shop.webhooks.settings")
    def test_verify_signature_debug_mode(self, mock_settings):
        """En mode debug, la signature est toujours valide"""
        mock_settings.PAYPAL_DEBUG = True
        mock_settings.PAYPAL_MODE = "sandbox"

        result = verify_paypal_signature({}, b"{}", "webhook_id")
        self.assertTrue(result)

    @patch("shop.webhooks.settings")
    def test_verify_signature_missing_headers(self, mock_settings):
        """Headers manquants en mode production"""
        mock_settings.PAYPAL_DEBUG = False
        mock_settings.PAYPAL_MODE = "production"

        result = verify_paypal_signature({}, b"{}", "webhook_id")
        self.assertFalse(result)

    @patch("shop.webhooks.settings")
    def test_verify_signature_sandbox_mode(self, mock_settings):
        """En mode sandbox, la signature est ignorée"""
        mock_settings.PAYPAL_DEBUG = False
        mock_settings.PAYPAL_MODE = "sandbox"

        result = verify_paypal_signature({}, b"{}", "webhook_id")
        self.assertTrue(result)


class ExtractOrderIdTests(TestCase):
    """Tests pour l'extraction de l'order_id"""

    def test_extract_from_invoice_id_with_prefix(self):
        """Extraction depuis invoice_id avec prefix ORDER-"""
        payload = {"resource": {"invoice_id": "ORDER-12345"}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertEqual(result, 12345)

    def test_extract_from_invoice_id_without_prefix(self):
        """Extraction depuis invoice_id sans prefix"""
        payload = {"resource": {"invoice_id": "12345"}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertEqual(result, 12345)

    def test_extract_from_purchase_units_invoice_id(self):
        """Extraction depuis purchase_units[0].invoice_id"""
        payload = {"resource": {"purchase_units": [{"invoice_id": "ORDER-67890"}]}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertEqual(result, 67890)

    def test_extract_from_custom_id(self):
        """Extraction depuis custom_id"""
        payload = {"resource": {"custom_id": "54321"}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertEqual(result, 54321)

    def test_extract_from_purchase_units_custom_id(self):
        """Extraction depuis purchase_units[0].custom_id"""
        payload = {"resource": {"purchase_units": [{"custom_id": "98765"}]}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertEqual(result, 98765)

    def test_extract_invalid_invoice_id(self):
        """Invoice_id invalide"""
        payload = {"resource": {"invoice_id": "not-a-number"}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertIsNone(result)

    def test_extract_no_id_found(self):
        """Aucun ID trouvé"""
        payload = {"resource": {}}
        result = extract_order_id_from_paypal_payload(payload)
        self.assertIsNone(result)


class CheckoutOrderCompletedTests(TestCase):
    """Tests pour handle_checkout_order_completed"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.category = Category.objects.create(
            name="Test Category", slug="test-category"
        )

        self.book = Book.objects.create(
            title="Test Book",
            slug="test-book",
            price=29.99,
            stock_quantity=10,
            category=self.category,
        )

        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-2024-001",
            status="pending",
            payment_status="pending",
            subtotal=29.99,
            shipping_cost=5.90,
            tax_amount=1.65,
            total_amount=37.54,
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address="123 Test St",
            shipping_city="Paris",
            shipping_postal_code="75001",
            shipping_country="France",
        )

        self.payment = Payment.objects.create(
            order=self.order,
            payment_method="paypal",
            amount=37.54,
            currency="EUR",
            status="pending",
        )

    @patch("shop.webhook_handlers.CartService.clear_cart")
    @patch("shop.webhook_handlers.OrderEmailService.send_payment_confirmed_email")
    def test_handle_checkout_order_completed_success(self, mock_email, mock_clear_cart):
        """Traitement réussi d'une commande complétée"""
        payload = {
            "resource": {
                "id": "PAYPAL-ORDER-123",
                "invoice_id": f"ORDER-{self.order.id}",
                "payer": {"payer_id": "PAYER-123"},
            }
        }

        result = handle_checkout_order_completed(payload)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.order.id)

        # Vérifier que la commande est mise à jour
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "confirmed")
        self.assertEqual(self.order.payment_status, "paid")

        # Vérifier que le paiement est mis à jour
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "completed")
        self.assertEqual(self.payment.paypal_payment_id, "PAYPAL-ORDER-123")
        self.assertEqual(self.payment.paypal_payer_id, "PAYER-123")

        # Vérifier que le panier est vidé
        mock_clear_cart.assert_called_once_with(self.user)

        # Vérifier que l'email est envoyé
        mock_email.assert_called_once()

    def test_handle_already_confirmed_order(self):
        """Commande déjà confirmée - doit retourner la commande sans modification"""
        self.order.status = "confirmed"
        self.order.save()

        payload = {
            "resource": {
                "id": "PAYPAL-ORDER-123",
                "invoice_id": f"ORDER-{self.order.id}",
            }
        }

        result = handle_checkout_order_completed(payload)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.order.id)

    def test_handle_cancelled_order(self):
        """Commande annulée - ne doit pas être traitée"""
        self.order.status = "cancelled"
        self.order.save()

        payload = {
            "resource": {
                "id": "PAYPAL-ORDER-123",
                "invoice_id": f"ORDER-{self.order.id}",
            }
        }

        result = handle_checkout_order_completed(payload)

        self.assertIsNone(result)

    def test_handle_nonexistent_order(self):
        """Commande inexistante"""
        payload = {"resource": {"id": "PAYPAL-ORDER-123", "invoice_id": "ORDER-99999"}}

        result = handle_checkout_order_completed(payload)

        self.assertIsNone(result)


class WebhookEndpointTests(TestCase):
    """Tests pour l'endpoint webhook"""

    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse("shop:paypal_webhook")

    def test_webhook_get_not_allowed(self):
        """GET n'est pas autorisé sur le webhook"""
        response = self.client.get(self.webhook_url)
        self.assertEqual(response.status_code, 405)

    @patch("shop.webhooks.verify_paypal_signature")
    def test_webhook_invalid_signature(self, mock_verify):
        """Signature invalide"""
        mock_verify.return_value = False

        response = self.client.post(
            self.webhook_url, data=json.dumps({}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")

    def test_webhook_invalid_json(self):
        """JSON invalide"""
        with patch("shop.webhooks.verify_paypal_signature") as mock_verify:
            mock_verify.return_value = True

            response = self.client.post(
                self.webhook_url, data="not valid json", content_type="application/json"
            )

            self.assertEqual(response.status_code, 400)

    @patch("shop.webhooks.verify_paypal_signature")
    def test_webhook_missing_event_data(self, mock_verify):
        """Données d'événement incomplètes"""
        mock_verify.return_value = True

        response = self.client.post(
            self.webhook_url,
            data=json.dumps({"resource": {}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("shop.webhooks.verify_paypal_signature")
    @patch("shop.webhooks.handle_checkout_order_completed")
    def test_webhook_checkout_order_completed(self, mock_handler, mock_verify):
        """Webhook CHECKOUT.ORDER.COMPLETED"""
        mock_verify.return_value = True
        mock_handler.return_value = MagicMock(id=123)

        payload = {
            "id": "EVENT-123",
            "event_type": "CHECKOUT.ORDER.COMPLETED",
            "resource_type": "checkout-order",
            "resource": {"id": "PAYPAL-ORDER-123", "invoice_id": "ORDER-123"},
        }

        response = self.client.post(
            self.webhook_url, data=json.dumps(payload), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Vérifier que l'événement est stocké
        event = WebhookEvent.objects.get(event_id="EVENT-123")
        self.assertEqual(event.event_type, "CHECKOUT.ORDER.COMPLETED")
        self.assertEqual(event.status, "processed")

        # Vérifier que le handler est appelé
        mock_handler.assert_called_once()

    @patch("shop.webhooks.verify_paypal_signature")
    @patch("shop.webhooks.handle_payment_capture_refunded")
    def test_webhook_payment_capture_refunded(self, mock_handler, mock_verify):
        """Webhook PAYMENT.CAPTURE.REFUNDED"""
        mock_verify.return_value = True
        mock_handler.return_value = True

        payload = {
            "id": "EVENT-456",
            "event_type": "PAYMENT.CAPTURE.REFUNDED",
            "resource_type": "capture",
            "resource": {"id": "REFUND-123"},
        }

        response = self.client.post(
            self.webhook_url, data=json.dumps(payload), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Vérifier que l'événement est stocké
        event = WebhookEvent.objects.get(event_id="EVENT-456")
        self.assertEqual(event.status, "processed")

    @patch("shop.webhooks.verify_paypal_signature")
    def test_webhook_unknown_event_type(self, mock_verify):
        """Type d'événement inconnu - doit être ignoré"""
        mock_verify.return_value = True

        payload = {
            "id": "EVENT-789",
            "event_type": "UNKNOWN.EVENT",
            "resource_type": "unknown",
            "resource": {},
        }

        response = self.client.post(
            self.webhook_url, data=json.dumps(payload), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        # Vérifier que l'événement est marqué comme ignoré
        event = WebhookEvent.objects.get(event_id="EVENT-789")
        self.assertEqual(event.status, "ignored")

    @patch("shop.webhooks.verify_paypal_signature")
    def test_webhook_duplicate_event(self, mock_verify):
        """Événement déjà traité"""
        mock_verify.return_value = True

        # Créer un événement existant
        WebhookEvent.objects.create(
            event_id="EVENT-999",
            event_type="CHECKOUT.ORDER.COMPLETED",
            resource_type="checkout-order",
            payload={},
            status="processed",
        )

        payload = {
            "id": "EVENT-999",
            "event_type": "CHECKOUT.ORDER.COMPLETED",
            "resource_type": "checkout-order",
            "resource": {},
        }

        response = self.client.post(
            self.webhook_url, data=json.dumps(payload), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["message"], "Already processed")


class WebhookEventModelTests(TestCase):
    """Tests pour le modèle WebhookEvent"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.order = Order.objects.create(
            user=self.user,
            order_number="ORD-2024-001",
            status="confirmed",
            payment_status="paid",
            subtotal=29.99,
            shipping_cost=5.90,
            tax_amount=1.65,
            total_amount=37.54,
            shipping_first_name="John",
            shipping_last_name="Doe",
            shipping_address="123 Test St",
            shipping_city="Paris",
            shipping_postal_code="75001",
            shipping_country="France",
        )

        self.event = WebhookEvent.objects.create(
            event_id="EVT-12345",
            event_type="CHECKOUT.ORDER.COMPLETED",
            resource_type="checkout-order",
            payload={"test": "data"},
            status="pending",
            order=self.order,
        )

    def test_mark_processed(self):
        """Test de la méthode mark_processed"""
        self.event.mark_processed()

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, "processed")
        self.assertIsNotNone(self.event.processed_at)

    def test_mark_failed(self):
        """Test de la méthode mark_failed"""
        error_msg = "Something went wrong"
        self.event.mark_failed(error_msg)

        self.event.refresh_from_db()
        self.assertEqual(self.event.status, "failed")
        self.assertEqual(self.event.error_message, error_msg)

    def test_str_representation(self):
        """Test de la représentation string"""
        expected = f"CHECKOUT.ORDER.COMPLETED - EVT-12345..."
        self.assertEqual(str(self.event), expected)
