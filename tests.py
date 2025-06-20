import unittest
import os

def test_leri_calistir():
    test_klasoru = 'unittest'
    yukleyici = unittest.TestLoader()
    test_paketi = yukleyici.discover(start_dir=test_klasoru)

    test_kosucusu = unittest.TextTestRunner(verbosity=2)
    test_sonucu = test_kosucusu.run(test_paketi)

    return test_sonucu.wasSuccessful()

if __name__ == '__main__':
    basarili = test_leri_calistir()
    if basarili:
        print("Tüm testler başarıyla geçti.")
    else:
        print("Bazı testler başarısız oldu.")