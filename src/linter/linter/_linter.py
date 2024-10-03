import json

from dotenv import dotenv_values

from src.linter.linter.error_management import ErrorManagement
from src.linter.linter.parser import Parser
from src.linter.linter.nodevisitor.node_visitor import NodeVisitor


class Linter:
    __slots__ = (
        "env",
        "config",
        "cnlp",
        "cnlp_ast_like",
        "cnlp_temp_types",
        "parser",
        "node_visitor",
        "error_management",
    )

    def __init__(self, cnlp: str, config: dict = None):
        self.env = dotenv_values()
        self.config = config
        self.cnlp = cnlp
        self.parser = Parser(env=self.env)
        self.error_management = ErrorManagement()
        self.cnlp_temp_types = {}
        self.cnlp_ast_like = None
        self.node_visitor = None

    def syntax_analysis(self):
        if self.config:
            pass

        syntax_analysis_result = self.parser.syntax_analysis(cnlp=self.cnlp)
        self.cnlp_ast_like = syntax_analysis_result['cnlp_ast_like']
        self.cnlp_temp_types = syntax_analysis_result['cnlp_temp_types']
        self.node_visitor = NodeVisitor(
            cnlp_temp_types=self.cnlp_temp_types,
            cnlp_ast_like=syntax_analysis_result['cnlp_ast_like']
        )
        self.parser.print_dict()
        for error in syntax_analysis_result['error_list']:
            self.error_management + error

    def semantic_analysis(self):
        if self.cnlp_ast_like is None:
            raise ValueError("No parsed AST found. Please perform grammatical analysis first.")

        error_list = (
                self.node_visitor.deal_temp_vars() +
                self.node_visitor.ref_check() +
                self.node_visitor.call_api_check()
        )

        for error in error_list:
            self.error_management + error


if __name__ == "__main__":
    cnlp = """   
[DEFINE_AGENT: FitnessHealthAdvisor]
    [DEFINE_PERSONA:]
        ROLE: You are a fitness and health assistant providing workout routines and diet plans based on user input.
    [END_PERSONA]

    [DEFINE_CONSTRAINTS:]
        FORBID: Share only safe and verified health tips, avoid any content that could harm the user.
    [END_CONSTRAINTS]

    [DEFINE_TYPES:]
        WorkoutType = ["strength", "cardio", "flexibility", "balance"]
        DietPlan = { meals: List[str], total_calories: int }
        WorkoutPlan = { exercises: List[str], duration_in_minutes: int, intensity: str }
        FeedbackResponse = ["great", "average", "poor"]
    [END_TYPES]

    [DEFINE_VARIABLES:]
        _user_account_fitness: FitnessUserInfo
        _chosen_workout_type: WorkoutType
        _diet_preference: str
        workout_plan: WorkoutPlan
        diet_plan: DietPlan
        feedback: FeedbackResponse
        _recommendation: str
    [END_VARIABLES]

    [DEFINE_WORKER: "Workout and Diet Planning" FitnessRoutineWorkflow]
        [INPUTS]
            <REF>_user_account_fitness</REF>
        [END_INPUTS]

        [OUTPUTS]
            <REF>_recommendation</REF>
        [END_OUTPUTS]

        [MAIN_FLOW]
            [SEQUENTIAL_BLOCK]
                COMMAND-1 [INPUT "What type of workout would you like to focus on? (strength, cardio, flexibility, balance)" VALUE _chosen_workout_type: WorkoutType SET]
                COMMAND-2 [CALL get_workout_plan WITH {user: <REF>_user_account_fitness</REF>, type: <REF>_chosen_workout_type</REF>} RESPONSE workout_plan: WorkoutPlan SET]
                COMMAND-3 [INPUT "Do you have any dietary preferences? (e.g., vegetarian, low-carb, high-protein)" VALUE _diet_preference: str SET]
                COMMAND-4 [CALL get_diet_plan WITH {user: <REF>_user_account_fitness</REF>, preference: <REF>workout_plan</REF>} RESPONSE diet_plan: DietPlan SET]
            [END_SEQUENTIAL_BLOCK]

            [IF <REF>_chosen_workout_type</REF> = "strength"]
                COMMAND-5 [DISPLAY "Your strength training workout plan includes: <REF>workout_plan</REF>"]
            [ELSEIF <REF>_chosen_workout_type</REF> = "cardio"]
                COMMAND-6 [DISPLAY "Your cardio workout plan includes: <REF>workout_plan</REF>"]
            [ELSEIF <REF>_chosen_workout_type</REF> = "flexibility"]
                COMMAND-7 [DISPLAY "Your flexibility training workout plan includes: <REF>workout_plan</REF>"]
            [ELSEIF <REF>_chosen_workout_type</REF> = "balance"]
                COMMAND-8 [DISPLAY "Your balance training workout plan includes: <REF>workout_plan</REF>"]
            [END_IF]

            [SEQUENTIAL_BLOCK]
                COMMAND-9 [DISPLAY "Your diet plan is: <REF>diet_plan</REF>"]
                COMMAND-10 [INPUT "How would you rate today's fitness plan? (great, average, poor)" VALUE feedback: FeedbackResponse SET]
            [END_SEQUENTIAL_BLOCK]

            [IF <REF>feedback</REF> = "great"]
                COMMAND-11 [COMMAND Set the value of _recommendation to "You did an excellent job today! Keep it up!" RESULT _recommendation: str SET]
            [ELSEIF <REF>feedback</REF> = "average"]
                COMMAND-12 [COMMAND Set the value of _recommendation to "You did well, but there's room for improvement!" RESULT _recommendation: str SET]
            [ELSEIF <REF>feedback</REF> = "poor"]
                COMMAND-13 [COMMAND Set the value of _recommendation to "Don't be discouraged. Tomorrow is another chance!" RESULT _recommendation: str SET]
            [END_IF]

            [SEQUENTIAL_BLOCK]
                COMMAND-14 [DISPLAY "Today's feedback: <REF>_recommendation</REF>"]
            [END_SEQUENTIAL_BLOCK]
        [END_MAIN_FLOW]
    [END_WORKER]
[END_AGENT]
"""

    linter = Linter(cnlp=cnlp)
    linter.syntax_analysis()
    linter.semantic_analysis()
    error_sum = linter.error_management.error_sum()
    print(json.dumps(error_sum, indent=4))

