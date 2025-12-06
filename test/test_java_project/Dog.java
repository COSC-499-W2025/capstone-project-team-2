package animals;

import java.util.ArrayList;
import java.util.List;

/**
 * Dog class demonstrating inheritance and polymorphism.
 */
public class Dog extends Animal {
    private String breed;
    private List<String> tricks;

    public Dog(String name, int age, String breed) {
        super(name, age);
        this.breed = breed;
        this.tricks = new ArrayList<>();
    }

    @Override
    public void speak() {
        System.out.println(getName() + " says: Woof!");
    }

    @Override
    public void move() {
        System.out.println(getName() + " runs on four legs");
    }

    public void fetch() {
        System.out.println(getName() + " fetches the ball!");
        learnTrick("fetch");
    }

    public void learnTrick(String trick) {
        tricks.add(trick);
        System.out.println(getName() + " learned: " + trick);
    }

    public List<String> getTricks() {
        return new ArrayList<>(tricks);
    }

    public String getBreed() {
        return breed;
    }

    // Nested loop for complexity testing
    public void performAllTricks(int times) {
        for (int i = 0; i < times; i++) {
            for (String trick : tricks) {
                System.out.println(getName() + " performs: " + trick);
            }
        }
    }
}
