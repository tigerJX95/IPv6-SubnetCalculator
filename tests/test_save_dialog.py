"""导出格式校验回归测试，无需启动图形界面。"""
import ast
import unittest
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / 'main.py').read_text(encoding='utf-8')
node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'determine_export_format')
namespace = {'Path': Path}
exec(compile(ast.Module(body=[node], type_ignores=[]), '<format-check>', 'exec'), namespace)
validate = namespace['determine_export_format']

class SaveDialogTests(unittest.TestCase):
    def test_normal_excel(self):
        self.assertEqual(validate(Path('export.xlsx'), False), 'xlsx')
    def test_normal_txt(self):
        self.assertEqual(validate(Path('export.txt'), False), 'txt')
    def test_uppercase_extension(self):
        self.assertEqual(validate(Path('export.TXT'), True), 'txt')
    def test_oversized_txt(self):
        self.assertEqual(validate(Path('export.txt'), True), 'txt')
    def test_oversized_excel_rejected(self):
        with self.assertRaises(ValueError): validate(Path('export.xlsx'), True)
    def test_unknown_extension_rejected(self):
        with self.assertRaises(ValueError): validate(Path('export.csv'), False)
