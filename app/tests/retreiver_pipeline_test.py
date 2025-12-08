from app.tests.db_test import db_test
from app.tests.personal_info_parser_test import parsing_test
from app.tests.personal_info_search_test import search_test

if __name__ == "__main__":
    if db_test():
        if parsing_test():
            if search_test():
                print("All tests has been passed")