class DataProcessor:
    def __init__(self, source):
        self.source = source

    def load(self):
        """Load raw data from a source. Base implementation."""
        try:
            with open(self.source, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Source file '{self.source}' not found.")

    def process(self, data):
        """Process data. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement the process() method.")

    def run(self):
        raw = self.load()
        return self.process(raw)


class UppercaseProcessor(DataProcessor):
    def process(self, data):
        """Convert text to uppercase."""
        if not isinstance(data, str):
            raise ValueError("Input data must be a string.")
        return data.upper()


class WordCountProcessor(DataProcessor):
    def process(self, data):
        """Count words in the text."""
        if not isinstance(data, str):
            raise ValueError("Input data must be a string.")
        words = data.split()
        return {
            "word_count": len(words),
            "unique_words": len(set(words)),
            "words": words
        }


class SafeProcessor(DataProcessor):
    def load(self):
        """Override to return empty string instead of error."""
        try:
            return super().load()
        except FileNotFoundError:
            return ""

    def process(self, data):
        """Fallback processor that just returns raw text."""
        return data


def main():
    processor1 = UppercaseProcessor("input.txt")
    processor2 = WordCountProcessor("input.txt")
    processor3 = SafeProcessor("missing.txt")

    try:
        print("Uppercase:", processor1.run())
    except Exception as e:
        print("Error:", e)

    try:
        print("Word Count:", processor2.run())
    except Exception as e:
        print("Error:", e)

    print("Safe Processor:", processor3.run())


if __name__ == "__main__":
    main()
