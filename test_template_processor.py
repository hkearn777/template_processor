import os
import tempfile
import unittest
from unittest.mock import patch

import template_processor as tp


class TemplateProcessorTests(unittest.TestCase):
    def test_apply_substitutions_with_wrapped_and_unwrapped_tags(self):
        content = "Hello <<NAME>>, welcome to <<CITY>>."
        substitutions = {
            "NAME": "Howard",
            "<<CITY>>": "London",
        }

        result = tp.apply_substitutions(content, substitutions)

        self.assertEqual(result, "Hello Howard, welcome to London.")

    def test_find_unreplaced_tags_returns_unique_sorted_names(self):
        content = "A <<BETA>> and <<ALPHA>> and <<BETA>>"
        self.assertEqual(tp.find_unreplaced_tags(content), ["ALPHA", "BETA"])

    def test_process_template_fail_on_unreplaced_raises_system_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_path = os.path.join(tmp, "input.txt")
            output_path = os.path.join(tmp, "output.txt")

            with open(template_path, "w", encoding="utf-8") as f:
                f.write("Hello <<NAME>> from <<CITY>>")

            with self.assertRaises(SystemExit) as cm:
                tp.process_template(
                    template_path,
                    output_path,
                    {"NAME": "Howard"},
                    fail_on_unreplaced=True,
                )

            self.assertEqual(cm.exception.code, 1)

    def test_load_substitutions_requires_json_object(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            tmp.write("[1,2,3]")
            tmp_path = tmp.name

        try:
            with self.assertRaises(SystemExit) as cm:
                tp.load_substitutions_from_file(tmp_path)
            self.assertEqual(cm.exception.code, 1)
        finally:
            os.remove(tmp_path)

    def test_main_parses_substitution_and_writes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_path = os.path.join(tmp, "template.txt")
            output_path = os.path.join(tmp, "out.txt")

            with open(template_path, "w", encoding="utf-8") as f:
                f.write("Build: <<VERSION>>")

            argv = [
                "template_processor.py",
                template_path,
                output_path,
                "-s",
                "VERSION=1.2.3",
            ]

            with patch("sys.argv", argv):
                tp.main()

            with open(output_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "Build: 1.2.3")

    def test_process_template_folder_processes_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = os.path.join(tmp, "in")
            output_dir = os.path.join(tmp, "out")
            os.makedirs(input_dir, exist_ok=True)

            with open(os.path.join(input_dir, "a.txt"), "w", encoding="utf-8") as f:
                f.write("A=<<X>>")
            with open(os.path.join(input_dir, "b.txt"), "w", encoding="utf-8") as f:
                f.write("B=<<Y>>")

            tp.process_template_folder(input_dir, output_dir, {"X": "1", "Y": "2"})

            with open(os.path.join(output_dir, "a.txt"), "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "A=1")
            with open(os.path.join(output_dir, "b.txt"), "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "B=2")

    def test_process_template_folder_fail_on_unreplaced_raises_system_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = os.path.join(tmp, "in")
            output_dir = os.path.join(tmp, "out")
            os.makedirs(input_dir, exist_ok=True)

            with open(os.path.join(input_dir, "a.txt"), "w", encoding="utf-8") as f:
                f.write("A=<<X>> and <<Z>>")

            with self.assertRaises(SystemExit) as cm:
                tp.process_template_folder(
                    input_dir,
                    output_dir,
                    {"X": "1"},
                    fail_on_unreplaced=True,
                )

            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
