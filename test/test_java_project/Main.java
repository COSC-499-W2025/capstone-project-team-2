package animals;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Main class demonstrating polymorphism and data structures.
 */
public class Main {
    public static void main(String[] args) {
        // Polymorphism - Animal references to Dog and Cat
        List<Animal> animals = new ArrayList<>();
        animals.add(new Dog("Buddy", 3, "Golden Retriever"));
        animals.add(new Cat("Whiskers", 5, true));
        animals.add(new Dog("Max", 2, "German Shepherd"));

        // HashMap usage
        Map<String, Animal> animalMap = new HashMap<>();
        for (Animal animal : animals) {
            animalMap.put(animal.getName(), animal);
        }

        // Polymorphic method calls
        System.out.println("=== All Animals ===");
        for (Animal animal : animals) {
            System.out.println(animal);
            animal.speak();
            animal.move();
            System.out.println();
        }

        // Type-specific operations
        System.out.println("=== Dog Tricks ===");
        Dog buddy = (Dog) animalMap.get("Buddy");
        buddy.fetch();
        buddy.learnTrick("roll over");
        buddy.performAllTricks(2);
    }
}
