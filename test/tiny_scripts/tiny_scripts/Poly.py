class Shape:
    def area(self):
        raise NotImplementedError("Subclasses must implement the area() method.")

    def describe(self):
        return "A generic shape with no specific form."


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * (self.radius ** 2)

    def describe(self):
        return f"A circle with radius {self.radius}."


class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def describe(self):
        return f"A rectangle measuring {self.width} x {self.height}."


class Triangle(Shape):
    def __init__(self, base, height):
        self.base = base
        self.height = height

    def area(self):
        return 0.5 * self.base * self.height

    def describe(self):
        return f"A triangle with base {self.base} and height {self.height}."


def print_shape_info(shape_obj):
    # Polymorphism happens here:
    # All objects share the same interface (area, describe)
    # but behave differently depending on their class.
    print("Description:", shape_obj.describe())
    print("Area:", shape_obj.area())


def main():
    shapes = [
        Circle(5),
        Rectangle(4, 10),
        Triangle(6, 3)
    ]

    for shape in shapes:
        print_shape_info(shape)
        print("-" * 20)


if __name__ == "__main__":
    main()
