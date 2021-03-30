import random

class MyEncryption:
    def __init__(self):
        self.encryption_data_structure = None
        while True:
            self.encryption_data_structure = self.create_new_encryption_data_structure()
            if not self.check_same_keys(self.encryption_data_structure):
                break

    @staticmethod
    def create_new_encryption_data_structure():
        # All of the keys
        keys = {
            'letters': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                        'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                        'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
                        'y', 'z', " "],
            'numbers': [str(num) for num in range(0, 10)],
            'spacial_characters': [
                '`',
                '~',
                '@',
                '!',
                '#',
                '%',
                '^',
                '&',
                '*',
                '(',
                ')',
                '-',
                '_',
                '+',
                '=',
                ':',
                '{',
                '}',
                '"',
                "$",
                "'",
                '[',
                ']',
                ";",
                '?',
                '<',
                '>',
                '.',
                ',',
                "/"
            ]
        }

        # Add capital letters.
        for letter in keys['letters']:
            if not letter.isupper() and letter != ' ' and letter != letter.upper():
                keys['letters'].append(letter.upper())

        chr_wrappers = [
            {'id': '1', 'chars': ['(__|', '}__|', '&|__']},
            {'id': '2', 'chars': ['(&(_|', '9)_|', '*7_|']},
            {'id': '3', 'chars': ['(-=_|', '$(*)', '^$_|']},
            {'id': '4', 'chars': ['({=|', '$(%|', '^$&|']},
        ]

        encryption_data_structure = letters_encryption = numbers_encryption = spacial_characters_encryption = {}
        used_chars = []
        # Get random chr_wrapper
        random_chr_wrapper = random.choice(chr_wrappers)['chars']
        # Encrypts all of the keys
        for (key, value) in keys.items():
            for character in value:
                if key == 'letters':
                    while True:
                        random_character = random.choice(value)
                        if random_character not in used_chars and not character == random_character:
                            letters_encryption[
                                character] = f'{random_chr_wrapper[0]}{random_character}{random_chr_wrapper[0]}'
                            used_chars.append(random_character)
                            break
                elif key == 'numbers':
                    while True:
                        random_character = random.choice(value)
                        if random_character not in used_chars and not character == random_character:
                            numbers_encryption[
                                character] = f'{random_chr_wrapper[1]}{random_character}{random_chr_wrapper[1]}'
                            used_chars.append(random_character)
                            break
                else:
                    while True:
                        random_character = random.choice(value)
                        if random_character not in used_chars and not character == random_character:
                            spacial_characters_encryption[
                                character] = f'{random_chr_wrapper[2]}{random_character}{random_chr_wrapper[2]}'
                            used_chars.append(random_character)
                            break
            used_chars = []

        def add_encrypted_dic(encrypted_dic):
            for (k, v) in encrypted_dic.items():
                encryption_data_structure[k] = v

        add_encrypted_dic(letters_encryption)
        add_encrypted_dic(numbers_encryption)
        add_encrypted_dic(spacial_characters_encryption)

        return encryption_data_structure

    def encrypt_data(self, data):
        encrypted_data = ''
        for d in data:
            for (key, value) in self.encryption_data_structure.items():
                if d == key:
                    encrypted_data += value
        return encrypted_data

    def decrypt_data(self, encrypted_data):
        decrypted_data = ''
        decrypting_key = ''

        for ed in encrypted_data:
            decrypting_key += ed
            for (key, value) in self.encryption_data_structure.items():
                if decrypting_key == value:
                    decrypted_data += key
                    decrypting_key = ""

        return decrypted_data

    @staticmethod
    def check_same_keys(encrypted_dic):
        """
            Returns if the same items having then True other wise False.
        :param encrypted_dic:
        :return:
        """
        privies_value = ""
        same_values = []
        count = 0
        items_len = 0
        for (key, value) in encrypted_dic.items():
            items_len += 1
            if privies_value == value:
                same_values.append({'key': key, 'value': value})
            else:
                count += 1

        return len(same_values) > 0
