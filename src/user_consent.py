import sys

# Data consent messages
CONSENT_HEADER = "\nData Usage Consent\n" + "-" * 50
CONSENT_REQUEST = """We need your permission to use the data you will upload in our system.
This data will be processed and analyzed as part of our mining system.
"""
CONSENT_PROMPT = "\nDo you consent to allow us to use your data? (yes/no): "
CONSENT_GRANTED = "\n✓ Thank you! Consent granted for data usage."

# External services consent messages
EXTERNAL_HEADER = "\nExternal Services Consent\n" + "-" * 50
EXTERNAL_REQUEST = """We can enhance our analysis using external services (e.g., LLM).

Privacy Implications:
- Data may be processed by third-party services
- Enhanced analysis capabilities
- Strict data handling protocols followed
- External processing is optional"""
EXTERNAL_PROMPT = "\nDo you consent to allow external services processing? (yes/no): "
EXTERNAL_GRANTED = "\n✓ Thank you! Your data will be processed with enhanced external services."
EXTERNAL_DENIED = "\nYou've chosen to proceed without external services. Analysis will be limited to local processing only."
EXTERNAL_DENIED_CONFIRM = "\nDo you want to continue with basic analysis (without external services)? (yes/no): "

# General messages
CONSENT_DENIED_WARNING = "\n⚠️  Without consent, we cannot proceed with data processing."
CONFIRM_EXIT_PROMPT = "Are you sure you want to exit? (yes/no): "
EXIT_MESSAGE = "\nThank you for your time. Exiting system."
RETRY_MESSAGE = "\nReturning to consent question..."
INVALID_INPUT = "\nInvalid input. Please answer with 'yes' or 'no'."
CONSENT_REVOKED = "\n⚠️  Consent has been revoked. Data access is now restricted."


class UserConsent:
    def __init__(self):
        """Initialize consent manager with default consent values as False."""
        self.has_data_consent = False
        self.has_external_consent = False

    def ask_for_consent(self) -> bool:
        """
        Ask user for consent to use their data and optionally use external services.
        Handles the consent flow with retry logic for invalid inputs.

        Returns:
            bool: True if user gave at least data consent, False if user denied completely
        """
        # First ask for data consent
        if not self._ask_for_data_consent():
            return False

        # If data consent granted, ask for external services consent
        if not self._ask_for_external_consent():
            return False  # User chose to exit when declining external services

        return True

    def _ask_for_data_consent(self) -> bool:
        """
        Ask user for data usage consent.
        
        Returns:
            bool: True if user gave consent, False if denied
        """
        while True:
            print(CONSENT_HEADER)
            print(CONSENT_REQUEST)
            consent_answer = input(CONSENT_PROMPT).lower().strip()

            if consent_answer in ['yes', 'y']:
                self.has_data_consent = True
                print(CONSENT_GRANTED)
                return True

            elif consent_answer in ['no', 'n']:
                while True:
                    print(CONSENT_DENIED_WARNING)
                    confirm_exit = input(CONFIRM_EXIT_PROMPT).lower().strip()

                    if confirm_exit in ['yes', 'y']:
                        self.has_data_consent = False
                        print(EXIT_MESSAGE)
                        return False
                    elif confirm_exit in ['no', 'n']:
                        print(RETRY_MESSAGE)
                        break
                    else:
                        print(INVALID_INPUT)
                continue
            
            else:
                print(INVALID_INPUT)
                continue

    def _ask_for_external_consent(self) -> bool:
        """
        Ask user for external services consent.
        Only called after data consent is granted.
        
        Returns:
            bool: True if user wants to continue (with or without external services),
                 False if user wants to exit completely
        """
        print(EXTERNAL_HEADER)
        print(EXTERNAL_REQUEST)
        
        while True:
            external_answer = input(EXTERNAL_PROMPT).lower().strip()

            if external_answer in ['yes', 'y']:
                self.has_external_consent = True
                print(EXTERNAL_GRANTED)
                return True

            elif external_answer in ['no', 'n']:
                self.has_external_consent = False
                print(EXTERNAL_DENIED)
                
                while True:
                    continue_answer = input(EXTERNAL_DENIED_CONFIRM).lower().strip()
                    
                    if continue_answer in ['yes', 'y']:
                        # User wants to continue with basic analysis
                        return True
                    elif continue_answer in ['no', 'n']:
                        # User wants to exit completely
                        self.has_data_consent = False
                        print(EXIT_MESSAGE)
                        return False
                    else:
                        print(INVALID_INPUT)
            
            else:
                print(INVALID_INPUT)
                continue

    def check_consent(self) -> tuple[bool, bool]:
        """
        Check if we have user consent for data usage and external services.

        Returns:
            tuple[bool, bool]: (data_consent, external_consent)
        """
        return self.has_data_consent, self.has_external_consent

    def revoke_consent(self, include_external: bool = True):
        """
        Revoke previously granted consent.
        
        Args:
            include_external (bool): If True, also revoke external services consent
        """
        self.has_data_consent = False
        if include_external:
            self.has_external_consent = False
        print(CONSENT_REVOKED)


if __name__ == "__main__":
    consent_manager = UserConsent()
    
    # Ask for consent if we don't have it
    if not consent_manager.ask_for_consent():
        sys.exit(1)
    
    # Get final consent status
    data_consent, external_consent = consent_manager.check_consent()
    
    # Show appropriate message based on consent levels
    if external_consent:
        print("\nProceeding with system operations using external services...")
    else:
        print("\nProceeding with basic system operations (no external services)...")