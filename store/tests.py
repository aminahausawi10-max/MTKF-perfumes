from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Brand, Category, Product

class AuthRedirectTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Chanel")
        self.category = Category.objects.create(name="Eau de Parfum")
        self.product = Product.objects.create(
            name="Bleu de Chanel",
            description="Woody fragrance",
            price="145.00",
            brand=self.brand,
            category=self.category,
            stock=10
        )
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.staff_user = User.objects.create_user(username="staffuser", password="staffpassword", is_staff=True)

    def test_anonymous_user_redirected_to_login(self):
        """Verify that anonymous users are redirected to login."""
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_authenticated_user_can_access_catalog(self):
        """Verify that authenticated users can see the catalog."""
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 200)

    def test_non_staff_cannot_access_admin_dashboard(self):
        """Verify that standard users are redirected when accessing admin pages."""
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302) # Redirect to login page for permissions check

    def test_staff_can_access_admin_dashboard(self):
        """Verify that staff users can access the admin dashboard."""
        self.client.login(username="staffuser", password="staffpassword")
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
