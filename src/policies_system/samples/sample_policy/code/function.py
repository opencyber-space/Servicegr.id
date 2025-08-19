import requests


def tell_fact():
    try:
        response = requests.get('https://catfact.ninja/fact')
        return response.json()['fact']
    except Exception as e:
        raise e


class AIOSv1PolicyRule:
    
    def __init__(self, rule_id, settings, parameters):
        """
        Initializes an AIOSv1PolicyRule instance.

        Args:
            rule_id (str): Unique identifier for the rule.
            settings (dict): Configuration settings for the rule.
            parameters (dict): Parameters defining the rule's behavior.
        """
        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters

    def eval(self, parameters, input_data, context):
        """
        Evaluates the policy rule.

        This method should be implemented by subclasses to define the rule's logic. 
        It takes parameters, input data, and a context object to perform evaluation.

        Args:
            parameters (dict): The current parameters.
            input_data (any): The input data to be evaluated.
            context (dict): Context (external cache), this can be used for storing and accessing the state across multiple runs.
        """

        # the input_data dict can be modified by the policy
        # DO input_data dict modifications here

        return {
            "allowed": True,
            "input_data": input_data
        }
        

