from create_dataclass import create_dataclass

FILES_DATA = [
    ("inference_config.yaml", "inference_config.py"),
    ("jumpstart_model.yaml", "jumpstart_model.py")
]

def generate_model_spec_classes():
    for input_file, output_file in FILES_DATA:
        create_dataclass(input_file, output_file)

if __name__ == '__main__':
    generate_model_spec_classes()

