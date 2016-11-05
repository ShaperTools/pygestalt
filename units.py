# pyGestalt Units Library

"""A set of common measurement units typically associated with numbers.

NOTE: The user should avoid doing substantial math using the dimensional dFloat type defined here.
It is inefficient and is largely intended to keep things straight and avoid unit mistakes when
defining machine kinematics or performing analysis.
"""

from pygestalt import errors
import math
import copy

class unit(object):
    """The base class for all measurement units."""
    def __init__(self, abbreviation, fullName, baseUnit = None, conversion = None):
        """Generates a new unit type.
        
        abbreviation -- a shorthand abbreviation for the unit, which will show up when printed. E.g. 'mm'.
        fullName -- a full name for the unit, e.g. 'millimeters'.
        baseUnit -- A unit type from which this unit a scalar multiple. For example, if this unit was millimeters, the base unit might be meters.
        conversion -- The conversion factor to get from the base unit to this unit. thisUnit = conversion*baseUnit.
            -- If conversion is None, this will be treated as a base unit.
            -- If conversion is 0, this will be treated as a non-dimensional unit.
        """
        self.abbreviation = abbreviation
        self.fullName = fullName
        self.baseUnit = baseUnit
        self.conversion = conversion
    
    def __call__(self, value):
        """Generates a new dFloat with the units of this unit object.
        
        value -- a floating point value for the dimensional number.
        """
        
        return dFloat(value, {self:1})
    
    def __mul__(self, value):
        """Left multiply for units.
        
        Gets called when a number or unit is directly multiplied by a unit to create a dFloat.
        """
        if type(value) == unit:
            return dFloat(1, {value:1, self:1})
        elif type(value) == dFloat:
            return value*self
        else:
            return dFloat(value, {self:1})        
        
        
    def __rmul__(self, value):
        """Right multiply for units.
        
        Gets called when a number or unit is directly multiplied by a unit to create a dFloat.
        """
        if type(value) == unit:
            return dFloat(1, {value:1, self:1})
        else:
            return dFloat(value, {self:1})
    
    def __rdiv__(self, value):
        """Right divide for units.
        
        Gets called when a number or unit is directly divided by a unit to create a dFloat.
        """
        
        if type(value) == unit:
            return dFloat(1, {value:1, self:-1})
        else:
            return dFloat(value, {self:-1})

    def __div__(self, value):
        """Divide for units.
        
        Gets called when a unit is directly divided by a unit or number to create a dFloat.
        """
        
        if type(value) == unit:
            return dFloat(1, {value:-1, self:1})
        elif type(value) == dFloat:
            return dFloat(1, {self:1})/value
        else:
            return dFloat(1.0/value, {self:1})
    
    def __pow__(self, power):
        """Power for units.
        
        Gets called when a unit is brought to a power, to create a dFloat."""
        return dFloat(1, {self:power})


class unitDictionary(dict):
    """A dictionary subclass used to store units and their powers."""
    def __init__(self, inputDictionary = {}):
        """Initialization function for unit dictionary.
        
        inputDictionary -- a seed dictionary in the form {unitObject:unitPower,...}
        """
        dict.__init__(self, inputDictionary)
    
    def __mul__(self, inputUnitDict):
        """Overrides multiplication to mix units into the dictionary.
        
        inputUnitDict -- a set of units either of unitDictionary type or in the same format: {unitObject:unitPower,...}
        """
        outputUnitDict = copy.copy(self) #work on a copy of self
        
        if type(inputUnitDict) == unitDictionary or type(inputUnitDict) == dict: #make sure that input is compatible
            for thisUnit in inputUnitDict: #iterate over keys in the input dictionary
                if thisUnit in outputUnitDict: #unit already exists in self
                    outputUnitDict.update({thisUnit: outputUnitDict[thisUnit] + inputUnitDict[thisUnit]}) #add powers to units
                    if outputUnitDict[thisUnit] == 0: outputUnitDict.pop(thisUnit) #if resulting power is 0, remove unit
                else:
                    outputUnitDict.update({thisUnit: inputUnitDict[thisUnit]}) #add new unit to dictionary
        else:
            raise errors.UnitError("Cannot make new unit dictionary using provided input")
        
        return outputUnitDict
    
    def __div__(self, inputUnitDict):
        """Overrides division to mix units into the dictionary.
        
        inputUnitDict -- a set of units of unitDictionary type or in the same format {unitObject:unitPower,...}
        """
        outputUnitDict = copy.copy(self) #work on a copy of self
        
        if type(inputUnitDict) == unitDictionary or type(inputUnitDict) == dict: #make sure that input is compatible
            for thisUnit in inputUnitDict: #iterate over keys in the input dictionary
                if thisUnit in outputUnitDict: #unit already exists in self
                    outputUnitDict.update({thisUnit: outputUnitDict[thisUnit] - inputUnitDict[thisUnit]}) #add powers to units
                    if outputUnitDict[thisUnit] == 0: outputUnitDict.pop(thisUnit) #if resulting power is 0, remove unit
                else:
                    outputUnitDict.update({thisUnit: -inputUnitDict[thisUnit]}) #add new unit to dictionary
        
        return outputUnitDict  
    
    def __rdiv__(self, other):
        """Overrides right-hand division. This is only used to invert units.
        other -- whatever the left-hand multiplier is. Doesn't matter as it doesn't get used.
        """
        outputUnitDict = copy.copy(self) #work on a copy of self
        
        for thisUnit in outputUnitDict: #iterate over keys in the output dictionary
            outputUnitDict.update({thisUnit:-outputUnitDict[thisUnit]})
        
        return outputUnitDict
    
    def __pow__(self, power):
        """Overrides power operator.
        
        power -- the power to which to raise the units."""
        
        outputUnitDict = copy.copy(self) #work on a copy of self
        
        for thisUnit in outputUnitDict: #iterate over keys in the output dictionary
            outputUnitDict.update({thisUnit: power * outputUnitDict[thisUnit]})
            
        return outputUnitDict
               

    def __str__(self):
        """String representation of the unit dictionary."""
        numeratorUnitList = filter(lambda unitPower: self[unitPower] > 0, self)
        denominatorUnitList = filter(lambda unitPower: self[unitPower] < 0, self)
         
        returnString = '' #this is the seed of the return string that will be built upon
         
        #fill in numerator string if no units are in the numerator
        if numeratorUnitList == [] and denominatorUnitList != []:
            returnString += "1"
         
        #fill in numerator string
        for numeratorUnit in numeratorUnitList: #iterate over all units in numerator
            if self[numeratorUnit] > 1: #more than to the first power
                returnString += numeratorUnit.abbreviation + '^' + str(self[numeratorUnit]) + '*'
            else:
                returnString += numeratorUnit.abbreviation + '*'
         
        if numeratorUnitList != []: returnString = returnString[:-1] #remove trailing *
         
        if denominatorUnitList != []: returnString += '/' #add trailing /
         
        for denominatorUnit in denominatorUnitList: #iterate over all units in denominator
            if self[denominatorUnit] < -1: #more than to the first power
                returnString += denominatorUnit.abbreviation + '^' + str(-self[denominatorUnit]) + '*'
            else:
                returnString += denominatorUnit.abbreviation + '*'
         
        if denominatorUnitList != []: returnString = returnString[:-1] #remove trailing *
         
        return returnString


class dFloat(float):
    """A dimensional floating-point number, i.e. a float with units."""
    
    def __new__(self, value, units = {}):
        """Constructor for dFloat that overrides float.__new__
        
        value -- the value of the floating point number.
        units -- a unitDictionary specifying the units for the new dFloat
        """
        return float.__new__(self, value)
    
    def __init__(self, value, units = {}):
        """Initializes the dFloat.
        
        units -- a dictionary containing key pairs of {unitObject: power} for all units
        """
        
        self.units = unitDictionary(units)
            
    def __str__(self):
        """String representation of the dFloat number"""
        
        return str(float(self)) + ' ' + str(self.units)
    
    def baseUnits(self):
        return reduceToBaseUnits(self)
    
    def convert(self, targetUnits):
        return convertToUnits(self, targetUnits)
    
    #--- OVERRIDE MATH FUNCTIONS ---
    def __add__(self, other):
        """Overrides addition.
        
        other -- the right-hand number to add
        
        A unit check will be performed if right-hand operand is of type dFloat. Otherwise the units
        of this dFloat will be passed along into the result.
        """
        value = float(self) + float(other) #perform numerical addition
        units = unitDict(self.units) #make a copy of unit dictionary
        if type(other) == dFloat:
            if self.units != other.units: #check to make sure units match
                raise errors.UnitError("addition operand units don't match")
        return dFloat(value, units)
    
    def __radd__(self, other):
        """Overrides right-handed addition.
        
        other -- the left-hand number to add.
        
        The units of this dFloat will be passed along into the result.
        """
        value = float(self) + float(other)
        units = unitDict(self.units)
        return dFloat(value, units)
    
    def __sub__(self, other):
        """Overrides subtraction.
        
        other -- the right-hand number to subract.

        A unit check will be performed if right-hand operand is of type dFloat. Otherwise the units
        of this dFloat will be passed along into the result.
        """
        value = float(self) - float(other) #perform numerical addition
        units = unitDict(self.units) #make a copy of unit dictionary
        if type(other) == dFloat:
            if self.units != other.units: #check to make sure units match
                raise errors.UnitError("addition operand units don't match")
        return dFloat(value, units)        
        
    def __rsub__(self, other):
        """Overrides right-handed subtraction.
        
        other -- the left-hand number to subtract.
        
        The units of this dFloat will be passed along into the result.
        """
        value = float(other) - float(self)
        units = unitDict(self.units)
        return dFloat(value, units)
    
    def __mul__(self, other):
        """Overrides left-hand multiplication.
        
        other -- right-hand number to be multiplied.
        """
        if type(other) != unit: #not multiplying by a generic unit
            value = float(self) * float(other) #perform numerical multiplication
            if type(other) == dFloat: #mix in units of other operand units
                newUnits = self.units*other.units
            else:
                newUnits = self.units
            return dFloat(value, newUnits)
        else:
            newUnits = self.units * {other:1}
            return dFloat(float(self), newUnits)
    
    def __rmul__(self, other):
        """Overrides right-hand multiplication.
        
        other -- left-hand number to be multiplied.
        
        Note that this will only be called if the left-hand number is not a dFloat.
        """
        if type(other) != unit: #not multiplying by a generic unit
            value = float(other) * float(self)
            return dFloat(value, self.units)
        else:
            newUnits = {other:1} * self.units
            return dFloat(value, newUnits)
    
    def __div__(self, other):
        """Overrides left-hand division.
        
        other -- the right-hand number to be divided by.
        """
        if type(other) != unit: #not dividing by a generic unit
            value = float(self)/ float(other) #perform numerical division
            if type(other) == dFloat: #mix in inverse of right-hand operand units
                newUnits = self.units / other.units
            else:
                newUnits = self.units
            return dFloat(value, newUnits)
        else:
            newUnits = self.units / {other:1}
            return dFloat(float(self), newUnits)
    
    def __rdiv__(self, other):
        """Overrides right-hand division.
        
        other -- the left-hand number to divide.
        
        Note that this will only be called if the left-hand number is not a dFloat.
        """
        if type(other) != unit: #not dividing by a generic unit
            value = float(other) / float(self)
            return dFloat(value, 1/self.units)   #inverted unit powers
        else:
            newUnits = (1 / self.units) * {other:1}
    
    def __pow__(self, other):
        """Overrides exponential.
        
        other -- the power to raise this value to.
        """
        value = float(self)**float(other)
        newUnits = self.units ** other
        return dFloat(value, newUnits)

#-- CONVERSION FUNCTIONS --
def getBaseUnits(derivedUnits):
    """Determines the base unit and scaling factor of a provided unit.
    
    Note that this function runs recursively until a base unit has been found
    
    Returns baseUnit, conversion, where:
        baseUnit -- the base unit of the provided derived units
        conversion -- the scaling factor to go from the base units to the provided derived units. derivedUnit = conversion*baseUnit
    """
    if type(derivedUnits.baseUnit) == unit: #it's a derived unit!
        baseUnit, conversion = getBaseUnits(derivedUnits.baseUnit)
        return baseUnit, derivedUnits.conversion*conversion
    else:
        return derivedUnits, 1.0

def reduceToBaseUnits(sourceNumber):
    """Reduces a dFloat into an equivalent in base units.
    
    sourceNumber -- a dFloat to be reduced.
    
    returns an equivalent dFloat whose units are the base units. 
    """
    if type(sourceNumber) != dFloat:
        raise errors.UnitError("Unable to reduce units. Must provide source number as a dFloat.")
        return False
    else:
        value = float(sourceNumber)
        units = sourceNumber.units #unitDictionary
        baseUnits = unitDictionary()
        for thisUnit in units: #iterate over units in unit dictionary
            baseUnit, conversionFactor = getBaseUnits(thisUnit)
            power = units[thisUnit] #the power to which the unit is raised
            baseUnits.update({baseUnit:power})
            value = value/(conversionFactor**power)
        return dFloat(value, baseUnits)      

def checkForEquivalentUnits(number1, number2):
    """Returns True if both provided numbers have equivalent units.
    
    number1, number2 -- dFloat numbers or unitDictionaries
    
    Note that this algorithm not only checks to see if the unit dictionaries are identical, but also takes into account
    non-dimensional units such as radians.
    """
    
    return True #JUST FOR NOW

def convertToUnits(sourceNumber, targetUnits):
    """Converts a number into target units if possible.
    
    sourceNumber -- a dFloat number to be converted
    targetUnits -- either a dFloat, unitDictionary, or unit
    
    returns a dFloat in the target units, or raises an exception if units mis-match.
    """
    
    sourceBaseNumber = reduceToBaseUnits(sourceNumber)

    if type(targetUnits) == unit: #target units are provided as a single unit type
        targetNumber = dFloat(1,{targetUnits:1})
    elif type(targetUnits) == unitDictionary: #target units are provided as a unit dictionary
        targetNumber = dFloat(1, targetUnits)
    elif type(targetUnits) == dFloat: #target units are provided as a dFloat
        targetNumber = targetUnits
    else: #target units are not provided as valid
        raise errors.UnitError("Unable to convert. " + str(targetUnits) + " is not a valid unit!")
        return False
    
    targetBaseNumber = reduceToBaseUnits(targetNumber) #reduce target units to base. This conveniently includes the multiplication factor
    
    if checkForEquivalentUnits(sourceBaseNumber, targetBaseNumber):
        conversionFactor = float(targetBaseNumber)
        return dFloat(float(sourceBaseNumber)/conversionFactor, targetNumber.units)
        
    

    
    
#-- STANDARD UNITS --

# distance
m = unit('m', 'meter') #meters are a base unit of distance
cm = unit('cm', 'centimeter', m, 100.0)
mm = unit('mm', 'millimeter', m, 1000.0)
inch = unit('in', 'inch', mm, 1.0/25.4)
ft = unit('ft', 'feet', inch, 1.0/12.0)
yd = unit('yd', 'yard', inch, 1.0/36.0)

# angle
rad = unit('rad', 'radian', 0) #radians are base unit of angle, and are dimensionless
deg = unit('deg', 'degree', rad, 180.0 / math.pi)
rev = unit('rev', 'revolution', rad, 1.0/(2.0*math.pi))

# time
s = unit('s', 'second') #seconds are base unit of time
min = unit('min', 'minute', s, 1.0/60.0)
hr = unit('hr', 'hour', s, 1.0/3600.0)

# mass
kg = unit('kg', 'kilogram') #kilograms are base unit of mass
g = unit('g', 'gram', kg, 1000.0)
oz = unit('oz', 'ounce', g, 0.035274)
lb = unit('lb', 'pound', oz, 1.0/16.0)

# force
N = unit('N', 'newton') #newtons are the base unit of force. Eventually need to build in a derived unit system to convert into SI base units.
kgf = unit('kgf', 'kilogram force', N, 1.0/9.80665)
gf = unit('gf', 'gram force', kgf, 1000.0)
ozf = unit('ozf', 'ounce force', gf, 0.035274)
lbf = unit('lbf', 'pound force', ozf, 1.0/16.0)