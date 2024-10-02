import dataclasses


@dataclasses.dataclass
class USABusinessOwners:
    data: str

    def __str__(self) -> str:
        return f"{self.data}"
