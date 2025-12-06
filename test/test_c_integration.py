"""Quick integration test for C analyzer in MultiLangOrchestrator."""

from pathlib import Path
from src.multilang_orchestrator import MultiLangOrchestrator
import tempfile
import json

# Sample C code with OOP patterns
c_code = '''
#include <stdlib.h>

typedef struct Animal {
    void (*speak)(void);
    void (*move)(void);
} Animal;

typedef struct Dog {
    Animal base;
    char* name;
} Dog;

Animal* animal_create(void) {
    return malloc(sizeof(Animal));
}

void animal_destroy(Animal* a) {
    free(a);
}

Dog* dog_new(const char* name) {
    Dog* d = malloc(sizeof(Dog));
    return d;
}

void dog_free(Dog* d) {
    free(d);
}
'''

def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write test C file
        c_file = Path(tmpdir) / "animal.c"
        c_file.write_text(c_code)
        print(f"Created test file: {c_file}\n")

        # Run orchestrator
        orchestrator = MultiLangOrchestrator(tmpdir)
        py_files, java_files, c_files = orchestrator.discover_files()

        print(f"Discovered files:")
        print(f"  Python: {len(py_files)}")
        print(f"  Java:   {len(java_files)}")
        print(f"  C:      {len(c_files)}")
        print()

        # Run full analysis
        metrics = orchestrator.analyze()

        print("Analysis Results:")
        print(json.dumps(metrics, indent=2, default=str))

if __name__ == "__main__":
    main()
