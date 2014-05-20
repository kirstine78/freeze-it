def is_note_valid(note_str):
    """ Takes in a string note_str and check if length is less
        than LIMIT_CHARS.
        Creates an object of classInfoEntered and returns it """

    LIMIT_CHARS = 36
    
    if note_str:
        if len(note_str) < LIMIT_CHARS:
            obj_note = info_entered.InfoEntered(True, "")  # create object of class InfoEntered
        else:
            obj_note = info_entered.InfoEntered(False, "Max. 35 characters")  # create object of class InfoEntered
    else:
        obj_note = info_entered.InfoEntered(True, "")  # create object of class InfoEntered
    return obj_note  



    
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
    LIMIT = 8
    # amount entered
    if amount:
        # amount has to be a number AND unit other than "" has to be chosen
        if is_amount_a_number(amount):
            if is_unit_chosen(unit):
                if len(str(amount)) < LIMIT:  # number is not too big
                    obj_amount = info_entered.InfoEntered(True, "")
                    return obj_amount
                else:  # the number is too big
                    obj_amount = info_entered.InfoEntered(False, "Max. 7 characters")
                    return obj_amount
            else:
                if len(str(amount)) < LIMIT:  # number is not too big
                    obj_amount = info_entered.InfoEntered(False, "")
                    return obj_amount
                else:  # the number is too big
                    obj_amount = info_entered.InfoEntered(False, "Max. 7 characters")
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
