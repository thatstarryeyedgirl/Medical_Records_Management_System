from aduncare.utils.validation import (
    validate_matric_number,
    get_department_from_matric
)


test_numbers = [
    "ADUN/FS/SEN/22/001",
    "ADUN/FS/CYB/23/015",
    "ADUN/FS/FRS/22/100",
    "ADUN/FS/COM/24/002",
    "ADUN/FS/BIO/23/010",
]


for matric in test_numbers:
    print(matric)
    print("Valid:", validate_matric_number(matric))
    print("Department:", get_department_from_matric(matric))
    print()
    