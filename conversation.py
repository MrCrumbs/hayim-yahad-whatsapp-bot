from helper import get_db, update_requested_contact, get_full_name, update_given_item, update_requsted_item

RETURN_TO_MAIN_MENU_STR = "\n\nלחזרה לתפריט הראשי בכל עת, שלח 0."


class Message(object):
    def __init__(self, incoming_message, user_context, logger):
        self.text = None
        self.incoming_message = incoming_message
        self.user_context = user_context
        self.logger = logger
    
    def execute(self):
        raise NotImplementedError


class IntroductionMessage(Message):
    def execute(self):
        self.text = "שלום לך! אזה כיף שפנית אלינו.\n" \
                    "*שמי בוטי, המענה האוטומטי של התכנית.*\n" \
                    "בואו נתחיל עם היכרות קצרה. נא כתבו את שמכם המלא?\n"
        self.user_context["next_conversation_phase"] = "MainMenuMessage"


class MainMenuMessage(Message):
    def execute(self):
        # check if we already know the user
        first_name, _ = get_full_name(self.incoming_message["From"], self.logger)
        if not first_name:
            full_name = self.incoming_message.get("Body", "")
            try:
                first_name, last_name = full_name.split()
                self.user_context["first_name"] = first_name
                self.user_context["last_name"] = last_name
            except Exception:
                self.text = "אנא כתבו את שמכם המלא, עם רווח בין השם הפרטי לשם המשפחה."
                self.user_context["next_conversation_phase"] = "MainMenuMessage"
                return
        self.text = "תודה {}! אנא בחרו מבין האפשרויות הבאות:\n" \
                    "אם ברצונכם למסור מוצר חשמלי או ריהוט - אנא שלחו 1.\n" \
                    "אם ברצונכם לקבל פריט - אנא שלחו 2.\n" \
                    "בא לכם לשמוע עוד על הפרויקט? אנא שלחו 3.\n" \
                    "רוצים שנחזור אליכם? אנא שלחו 4.\n".format(first_name)
        self.user_context["next_conversation_phase"] = "GiveOrReceiveMessage"


class GiveOrReceiveMessage(Message):
    def execute(self):
        try:
            selected_option = int(self.incoming_message.get("Body", None))
            if selected_option == 1:
                self.text = "מצוין! מה תרצו למסור?"
                self.user_context["next_conversation_phase"] = "GiveMessage"
            elif selected_option == 2:
                self.text = "מעולה, מה תרצו לקבל?"
                self.user_context["next_conversation_phase"] = "ReceiveMessage"
            elif selected_option == 3:
                self.text = "תוכנית 'חיים יחד' מבית גרעין יחד הינה תוכנית חברתית אשר מטרתה " \
                            "להגדיל את תחושת הערבות והשותפות בין התושבים, " \
                            "להצמיח פעילות ומנהיגות בנוער המתנדב של בית שאן והעמק, " \
                            "תוך עידוד מחזור מוצרי חשמל ורהיטים, ובכך גם לסייע לאחר וגם לשמור על סביבה נקיה וקיימות טובה יותר.\n" \
                            "התוכנית פועלת מ-2018, ובכל שבוע מתקיימים סבבים של העברות מכשור חשמלי ורהיטים \n" \
                            "מאנשים שרוצים למסור לאנשים שישמחו לקבל.\n" \
                            "*הפרויקט עובד בהתנדבות מלאה וללא עלות.*\n" \
                            "*אנו מעבירים רק ציוד תקין ב-100% ובמצב ראוי.*\n" \
                            "*כל אחד מוזמן להשתתף ולהעזר בתוכנית, ככל שנכיר יותר נרוויח יותר.*"
                self.user_context["next_conversation_phase"] = "MainMenuMessage"
            elif selected_option == 4:
                self.text = "תודה, אנחנו נחזור אליכם בקרוב!"
                self.user_context["next_conversation_phase"] = "MainMenuMessage"
                update_requested_contact(self.incoming_message["From"], self.logger)
            else:
                self.text = "המספר שבחרתם אינו מופיע באחת מהאפשרויות, אנא נסו שנית."
                self.user_context["next_conversation_phase"] = "GiveOrReceiveMessage"
        except Exception:
            self.text = "אנא בחרו במספר מתוך האפשרויות הקיימות."
            self.user_context["next_conversation_phase"] = "GiveOrReceiveMessage"


class GiveMessage(Message):
    def execute(self):
        given_item = self.incoming_message.get("Body", "")
        if given_item:
            self.text = "תודה רבה! כמעט סיימנו.\n" \
                        "אנא שלחו צילום של הפריט."
            self.user_context["given_item"] = given_item
            self.user_context["next_conversation_phase"] = "UploadImageMessage"
        else:
            self.text = "נראה שלא שלחתם את שם החפץ שברצונכם למסור.\n" \
                        "אנא כתבו לנו מה ברצונכם למסור."
            self.user_context["next_conversation_phase"] = "GiveMessage"


class ReceiveMessage(Message):
    def execute(self):
        receive_item = self.incoming_message.get("Body", "")
        if receive_item:
            self.text = "תודה! נחזור אליכם ברגע שנמצא מישהו שמוסר {}.\n".format(receive_item)
            self.user_context["next_conversation_phase"] = "MainMenuMessage"
            update_requsted_item(self.incoming_message["From"], receive_item, self.logger)
        else:
            self.text = "נראה שלא שלחתם את שם החפץ שברצונכם לקבל.\n" \
                        "אנא כתבו לנו מה ברצונכם לקבל."
            self.user_context["next_conversation_phase"] = "GiveMessage"


class UploadImageMessage(Message):
    def execute(self):
        images_num = int(self.incoming_message.get("NumMedia", 0))
        try:
            incoming_message = int(self.incoming_message.get("Body", ""))
            if incoming_message == 1:
                self.text = "מעולה. ניצור איתכם קשר כאשר נמצא התאמה לחפץ שברצונכם למסור."
                self.user_context["next_conversation_phase"] = "MainMenuMessage"
                update_given_item(self.incoming_message["From"], "", self.logger)
        except Exception:
            pass
        if images_num == 0:
            self.text = "לא קיבלתי תמונה של החפץ שברצונכם למסור.\n" \
                        "אם באפשרותכם לצרף תמונה, נא שלחו אותה כעת.\n" \
                        "אם לא, שלחו 1."
            self.user_context["next_conversation_phase"] = "UploadImageMessage"
        else:
            given_item_image_url = self.incoming_message.get("MediaUrl0", None)
            self.text = "תודה רבה! ניצור איתכם קשר כאשר נמצא התאמה לחפץ שברצונכם למסור.\n" \
                        "במידה והחפץ כבר לא רלוונטי, אנא עדכנו אותנו."
            self.user_context["next_conversation_phase"] = "MainMenuMessage"
            update_given_item(self.incoming_message["From"], given_item_image_url, self.logger)
