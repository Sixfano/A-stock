"""Optional OpenTDX provider placeholder."""
class OpenTDXProvider:
    enabled = False

    def health_check(self) -> bool:
        return self.enabled
