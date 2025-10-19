import sys

CONSENT_HEADER = "\nData Usage Consent\n" + "-" * 50
CONSENT_REQUEST = "We need your permission to use the data you will upload in our system.\nThis data will be processed and analyzed as part of our mining system."
CONSENT_PROMPT = "\nDo you consent to allow us to use your data? (yes/no): "
CONSENT_GRANTED = "\n✓ Thank you! Consent granted for data usage."
CONSENT_DENIED_WARNING = "\n⚠️  Without consent, we cannot proceed with data processing."
CONFIRM_EXIT_PROMPT = "Are you sure you want to exit? (yes/no): "
EXIT_MESSAGE = "\nThank you for your time. Exiting system."
RETRY_MESSAGE = "\nReturning to consent question..."
INVALID_INPUT = "\nInvalid input. Please answer with 'yes' or 'no'."
CONSENT_REVOKED = "\n⚠️  Consent has been revoked. Data access is now restricted."


class UserConsent:
    def __init__(self):
        """Initialize consent manager with default consent as False."""
        self.has_consent = False

    def ask_for_consent(self) -> bool:
        """
        Ask user for consent to use their data.
        Handles the consent flow with retry logic for invalid inputs.

        Returns:
            bool: True if user gave consent, False if user denied
        """
        while True:
            # Show consent information
            print(CONSENT_HEADER)
            print(CONSENT_REQUEST)
            consent_answer = input(CONSENT_PROMPT).lower().strip()

            if consent_answer in ['yes', 'y']:
                self.has_consent = True
                print(CONSENT_GRANTED)
                return True

            elif consent_answer in ['no', 'n']:
                # Ask for confirmation to exit
                while True:
                    print(CONSENT_DENIED_WARNING)
                    confirm_exit = input(CONFIRM_EXIT_PROMPT).lower().strip()

                    if confirm_exit in ['yes', 'y']:
                        self.has_consent = False
                        print(EXIT_MESSAGE)
                        return False
                    elif confirm_exit in ['no', 'n']:
                        # User doesn't want to exit, loop back to consent question
                        print(RETRY_MESSAGE)
                        break  # Break inner loop to go back to main consent question
                    else:
                        print(INVALID_INPUT)
                continue  # Continue outer loop to ask consent again
            
            else:
                print(INVALID_INPUT)
                continue  # Explicitly continue to ask the question again

    def check_consent(self) -> bool:
        """
        Check if we have user consent.

        Returns:
            bool: True if we have consent, False otherwise
        """
        return self.has_consent

    def revoke_consent(self):
        """Revoke previously granted consent."""
        self.has_consent = False
        print(CONSENT_REVOKED)


if __name__ == "__main__":
    consent_manager = UserConsent()
    
    # First check if we already have consent
    if not consent_manager.check_consent():
        # If no consent, ask for it
        if not consent_manager.ask_for_consent():
            sys.exit(1)
    
    print("Proceeding with system operations...")