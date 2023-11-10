from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from gh_automation_funda.config import Config

InputType = TypeVar("InputType")
IntermediateType = TypeVar("IntermediateType")
OutputType = TypeVar("OutputType")


class ETL(Generic[InputType, IntermediateType, OutputType], ABC):
    def __init__(self, config: Config) -> None:
        """
        Initialize the ETL object with the given configuration.
        """
        self.config: Config = config
        super().__init__()

    @abstractmethod
    def extract(self) -> InputType:
        """
        Extract data from a data source.
        Should return data in the form of InputType.
        """
        pass

    @abstractmethod
    def transform(self, data: InputType) -> IntermediateType:
        """
        Transform the extracted data.
        Should return data in the form of IntermediateType.
        """
        pass

    @abstractmethod
    def load(self, data: IntermediateType) -> OutputType:
        """
        Load the transformed data to a destination.
        Should return an indication of success/failure, in the form of OutputType.
        """
        pass


class AsyncETL(Generic[InputType, IntermediateType, OutputType], ABC):
    def __init__(self, config: Config) -> None:
        """
        Initialize the ETL object with the given configuration.
        """
        self.config: Config = config
        super().__init__()

    @abstractmethod
    async def extract(self) -> InputType:
        """
        Extract data from a data source.
        Should return data in the form of InputType.
        """
        pass

    @abstractmethod
    async def transform(self, data: InputType) -> IntermediateType:
        """
        Transform the extracted data.
        Should return data in the form of IntermediateType.
        """
        pass

    @abstractmethod
    async def load(self, data: IntermediateType) -> OutputType:
        """
        Load the transformed data to a destination.
        Should return an indication of success/failure, in the form of OutputType.
        """
        pass
