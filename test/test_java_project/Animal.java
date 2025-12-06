package animals;

/**
 * Base class demonstrating OOP patterns in Java.
 */
public abstract class Animal {
    private String name;
    private int age;

    public Animal(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Abstract methods for polymorphism
    public abstract void speak();
    public abstract void move();

    // Getters (encapsulation)
    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }

    @Override
    public String toString() {
        return name + " (" + age + " years old)";
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        Animal animal = (Animal) obj;
        return age == animal.age && name.equals(animal.name);
    }

    @Override
    public int hashCode() {
        return name.hashCode() * 31 + age;
    }
}
