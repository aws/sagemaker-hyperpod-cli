import warnings
# Reset warnings and show all except Pydantic serialization warnings
warnings.resetwarnings()
warnings.simplefilter("always")
# Suppress specific Pydantic serialization warnings globally (this is ignored due to customized parsing logic)
warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*serializer.*", category=UserWarning, module="pydantic")
# Suppress kubernetes urllib3 deprecation warning (this is internal dependencies)
warnings.filterwarnings("ignore", message=".*HTTPResponse.getheaders.*", category=DeprecationWarning, module="kubernetes")