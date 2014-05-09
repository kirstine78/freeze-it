from datetime import datetime
from datetime import date
import info_entered


def is_food_description_valid(food_description):
    """ Checks if food_description is not None and if length is > 0.
        Creates an object of classInfoEntered and returns it """

    if food_description and len(food_description) > 0:

        if len(food_description) > 499:
            obj_food = info_entered.InfoEntered(False, "'Food description' max. 500 characters")  # create object of class InfoEntered
            return obj_food
        else:
            obj_food = info_entered.InfoEntered(True, "")  # create object of class InfoEntered
            return obj_food
    else:
        obj_food = info_entered.InfoEntered(False, "You need a 'Food description'") # create object of class InfoEntered
        return obj_food
        

def is_measure_unit__valid(unit, amount):
    """ Checks if unit is valid in correspondance with amount.
        Creates an object of classInfoEntered and returns it """
    
    if unit == "":
        # amount have to be empty for unit to be valid, so check that
        if is_amount_entered(amount):
            obj_unit = info_entered.InfoEntered(False, "If you put in 'Amount' you also need 'Measuring unit'")
            return obj_unit
        else:
            # amount is empty
            obj_unit = info_entered.InfoEntered(True, "")
            return obj_unit

    else:  # Some unit other than ("") is chosen
        # then amount has to be entered AND valid, before unit will be valid
        if is_amount_entered(amount):
            obj_unit = info_entered.InfoEntered(True, "")
            return obj_unit
        else:  # amount not entered
            obj_unit = info_entered.InfoEntered(False, "")
            return obj_unit
            

def is_amount_valid(amount, unit):
    """ Checks if amount is valid in correspondance with unit.
        Creates an object of classInfoEntered and returns it """

    # amount entered
    if amount:
        # amount has to be a number AND unit other than "" has to be chosen
        if is_amount_a_number(amount):
            if is_unit_chosen(unit):
                obj_amount = info_entered.InfoEntered(True, "")
                return obj_amount
            else:
                obj_amount = info_entered.InfoEntered(False, "")
                return obj_amount
        else:
            obj_amount = info_entered.InfoEntered(False, "This is not a number!")
            return obj_amount
            
    # amount not entered
    else:
        # unit "" has to be chosen
        if is_unit_chosen(unit):
            obj_amount = info_entered.InfoEntered(False, "If you put in 'Measuring unit' you also need 'Amount'")
            return obj_amount
        else:
            obj_amount = info_entered.InfoEntered(True, "")
            return obj_amount


def is_exp_date_valid(a_date):
    """ Takes in a string in mm/dd/yyyy format, check if there is a date entered, if it is
        valid date, and if it is in the future. Returns an object of classInfoEntered """
    
    if a_date:
        try:
            datetime.strptime(a_date, '%m/%d/%Y')
            if is_future_date(a_date):
                obj_exp_date = info_entered.InfoEntered(True, "")
                return obj_exp_date
            else:
                obj_exp_date = info_entered.InfoEntered(False, "The entered date was in the past")
                return obj_exp_date
        except ValueError:
            obj_exp_date = info_entered.InfoEntered(False, "Incorrect data format, should be MM/DD/YYYY")
            return obj_exp_date
    else:
        obj_exp_date = info_entered.InfoEntered(True, "")
        return obj_exp_date

     
def are_all_validation_true(list_of_info_entered_objects):
    """ Takes in a list of objects and return True if all objects instance variable 'validation' are True """

    for item in list_of_info_entered_objects:
        if item.get_validation_info() == False:
            return False
    return True


##################################################################################################################


def is_unit_chosen(a_unit):
    """ Returns True if a_unit equals other than empty string ("") """

    if a_unit == "":
        return False
    else:
        return True
    

def is_amount_entered(an_amount):
    """ Returns True if an_amount is not None"""

    if an_amount:
        return True
    else:
        return False


def is_amount_a_number(an_amount):
    """ Return True if an_amount is a number """

    try:
        float(an_amount)
        return True
    except:
        return False


def upper_case(a_string):
    """ Return string with first letter in upper case """
    if a_string and len(a_string) > 0:
        if a_string[0:1] in "abcdefghijklmnopqrstuvwxyz":
            first_letter_to_upper = a_string[0:1].upper()
            if len(a_string) > 1:
                string_to_upper = first_letter_to_upper + a_string[1:]
            else:
                string_to_upper = first_letter_to_upper
            return string_to_upper
        else:
            return a_string
    else:
        return a_string


def is_future_date(a_date):
    """ Returns True if a_date mm/dd/yyyy is younger than current date yyyy-mm-dd """
    
    today = date.today() #yyyy-mm-dd
    
    #convert mm/dd/yyyy to YYYY-MM-DD
    exp_date_converted = datetime.strptime(a_date+" 12:00", "%m/%d/%Y %H:%M").date()

    return today <= exp_date_converted


def expires_soon(date_to_check):
    """ return boolean, int
        True if date_to_check yyyy-mm-dd is within 3 days to expire, and amount of days before exp """

    LIMIT_FOR_EXPIRES_SOON = 5

    
    today = date.today() #yyyy-mm-dd

    # difference between current date and date_to_check in format 'x days, 0:00:00'
    diff = date_to_check - today

    #convert to string
    diff_str =  str(diff)
    
    first_ch = diff_str[0:1]

    # split 'x days, 0:00:00' and put into list
    word_list = diff_str.split( )
    first_word = str(word_list[0]) # this is the number of days difference as string

    # expired
    if first_ch == "-": 
        return True, int(first_word)
    # expires today
    elif first_ch == "0":
        return True, 0
    # check if expires soon
    else:
        get_int = int(word_list[0])
        # expires soon
        if get_int <= LIMIT_FOR_EXPIRES_SOON:
            return True, int(first_word)
        # not to expire soon
        return False, int(first_word)

def convert_date_mmddyyyy(a_date):
    """ convert a_date with format yyyy-mm-dd to format mm/dd/yyyy"""

    mm = a_date[5:7]
    dd = a_date[-2:]
    yyyy = a_date[0:4]

    return mm + "/" + dd + "/" + yyyy
