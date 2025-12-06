package animals;

/**
 * Cat class demonstrating inheritance.
 */
public class Cat extends Animal {
    private boolean isIndoor;

    public Cat(String name, int age, boolean isIndoor) {
        super(name, age);
        this.isIndoor = isIndoor;
    }

    @Override
    public void speak() {
        System.out.println(getName() + " says: Meow!");
    }

    @Override
    public void move() {
        System.out.println(getName() + " walks gracefully");
    }

    public void scratch() {
        System.out.println(getName() + " scratches the furniture!");
    }

    public boolean isIndoor() {
        return isIndoor;
    }
}
