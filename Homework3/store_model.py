from typing import NoReturn


# class NegativeQuantity(Exception):
#     def __init__(
#         self,
#         msg="We have a problem! The products's quantity in stock cannot be negative!",
#     ):
#         self.message = msg
#         super().__init__(self.message)


class NotEnoughQuantity(Exception):
    def __init__(
        self,
        msg="The store doesn't have enough product!\nThe products's quantity in stock cannot be negative!",
    ):
        self.message = msg
        super().__init__(self.message)


class Product:
    def __init__(self, name: str, price: float, stock: int) -> NoReturn:
        self.name = name
        self.price = price
        self.stock = stock

    def __repr__(self) -> str:
        return f"It's {self.name}"

    def update_stock(self, quantity: int) -> str:
        try:
            self.stock -= quantity
            if self.stock < 0:
                self.stock += quantity
                raise NotEnoughQuantity
            else:
                print(
                    f"Quantity of product {self.name} in stock is {self.stock} pieces now."
                )
        except NotEnoughQuantity as exp:
            print(exp)
        # return self.stock - quantity


class Order:
    def __init__(self, order_products={}) -> NoReturn:
        self.order_products = order_products

    def add_products(self, product: Product, quantity: int) -> str:
        try:
            if product.stock - quantity < 0:
                raise NotEnoughQuantity
            else:
                self.order_products[product] = quantity
                print(
                    f"Product {product.name} in amount of {quantity} pieces added to order."
                )
                product.update_stock(quantity)
        except NotEnoughQuantity as exp1:
            print(exp1)

    def calculate_total(self):
        total = 0
        for product, quantity in self.order_products.items():
            total += quantity * product.price
        return total


class Store:

    def __init__(self, store_products=[]) -> NoReturn:
        self.store_products = store_products

    def __str__(self) -> str:
        return "The store is ready!"

    def add_product(self, product_added_to_store: Product) -> NoReturn:
        self.store_products.append(product_added_to_store)

    def list_products(self):
        for product in self.store_products:
            print(product.name, product.price, product.stock)

    def create_order(self):
        return Order()


if __name__ == "__main__":
    store = Store()

    product1 = Product("Laptop", 1000, 5)
    product2 = Product("Smartphone", 500, 10)

    store.add_product(product1)
    store.add_product(product2)

    store.list_products()

    order = store.create_order()
    print(order.order_products)

    order.add_products(product1, 6)
    order.add_products(product2, 11)

    print(order.order_products)
    print(order.calculate_total())

    store.list_products()
