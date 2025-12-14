from app.tests.db_test import db_test
from app.tests.parsing_test import parsing_test
from app.tests.search_test import search_test


def run_all_tests (verbose: bool = False) -> bool:
    tests = [
        ("Database test", db_test, (verbose,)),
        ("Parser test", parsing_test, (verbose,)),
        ("Personal data search", search_test, ("PERSONAL_DATA", verbose)),
        ("Project data search", search_test, ("PROJECT_DATA", verbose))
    ]
    
    all_passed = True
    
    
    for test_name, test_func, args in tests:
        result = test_func(*args)
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        
        if not result:
            all_passed = False
    
    
    if all_passed:
        print("All tests passed successfully")
        return True
    else:
        print("Some tests failed")
        return False

if __name__ == "__main__":
    run_all_tests (False)