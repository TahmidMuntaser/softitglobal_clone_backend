class OrderStatus:
    PENDING = "pending"
    DELIVERED = "delivered"

    CHOICES = [
        (PENDING, "Pending"),
        (DELIVERED, "Delivered"),
    ]