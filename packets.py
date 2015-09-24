#   pyGestalt Packets Module

"""Provides a fremework for templating, encoding, and decoding packets."""

#--IMPORTS--
from pygestalt import utilities
import itertools

class serializedPacket(list):
    """The type used for storing serialized packets.
    
    This type should act like a list while retaining a link to the template used to encode the packet.
    """
    def __init__(self, value = [], template = None):
        """Initialize a new packet.
        
        value -- an input list, or packet. Note that any meta-data such as template of an input packet will be lost.
        template -- the template used to generate this packet. Useful for updating etc...
        """
        list.__init__(self, utilities.flattenList(value))
        self.template = template
    
    def toString(self):
        """A shortcut to get the serialized packet in the format of a string."""
        return utilities.listToString(self)
    
    def toList(self):
        """A shortcut to get the serialized packet in the form of a stripped list."""
        
        
        
class template(object):
    """Stores the formatting used to encode and decode serialized data packets."""
    def __init__(self, *packetTokens):
        """Initialize a new template.
        
        packetTokens -- an ordered list of elements that comprise a packet. If the first argument is a string, it will be treated as the packet name.
        """
        
        if type(packetTokens[0]) == str:    # the first argument is a string. We'll assume that's the name of the template.
            self.name = packetTokens[0] # give this template a name!
            self.template = packetTokens[1:] # the internally stored template is just the list of arguments in the order they were provided, minus the name.
        else: 
            self.name = None  # a nameless template :-(
            self.template = packetTokens    # the internally stored template is just the list of arguments in the order they were provided. 

        self.template = list(self.template)
            
    def __call__(self, input):
        """A shortcut to either encode or decode a packet.
        
        Calling the template instance directly will have the effect of either
        encoding or decoding a packet, depending on the type provided as input.
        
        input -- if a dict, will return an encoded packet. If a list or packet, will return a decoded dictionary.
        """
        if type(input) == dict: # Provided input is a dictionary, so user wants to encode dictionary as packet.
            return self.encode(input)
        if type(input) == list or type(input) == packet:    # Provided input is a list or packet, so user wants to decode into a dictionary
            return self.decode(input)
    
    def encode(self, inputDict, *args, **kwargs):
        """Serializes a packet using the token list stored in self.template.
        
        inputDict -- the input dictionary that needs to get encoded using the template.
        *args and **kwargs -- here to catch unexpected terms because this encode function needs to be interchangeable with a packet
                              token to permit embedding packets.
        """
        
        #1) Encode tokens that don't require information on the in-process packet, i.e. NOT length and checksum tokens 
        inProcessPacket = [token.encode(inputDict, templateName = self.name) for token in self.template]
        
        #2) Encode length tokens, all others get copied without calling an encode method. At this point most tokens will be lists.
        inProcessPacket = [token.encode(inputDict, inProcessPacket, self.name) if type(token) == length else token for token in inProcessPacket]
        
        #3) Encode checksum tokens, all others get copied without calling an encode method.
        inProcessPacket = [token.encode(inputDict, inProcessPacket, self.name) if type(token) == checksum else token for token in inProcessPacket]
                    
        return serializedPacket(inProcessPacket, self)  #convert into packet type, giving a reference to the template, and return
    
    
    def decode(self):
        pass

class packetToken(object):
    """Base class for creating packet tokens, which are elements that handle encoding and decoding each segment of a packet."""
    
    def __init__(self, keyName, *args):
        """Initialize a new packet token.
        
        keyName -- a reference name for the token that will match a key in an encoding dictionary, or be provided as a key during decoding.
        """
        self.keyName = keyName  # permanently store keyName
        self.requireEncodeDict = True   #by default, tokens require an encode dictionary in order to encode packets. Exceptions include length and checksum tokens.
        self.init(*args)    # call subclass init function to do something with additional arguments.
    
    def init(self, *args):
        """Secondary initializer should be over-ridden by subclass.""" 
        pass
    
    def encode(self, encodeDict, inProcessPacket = [], templateName = None):
        """Serializes the value keyName in encodeDict using the subclass's _encode_ method.
        
        encodeDict -- a dictionary of values to be encoded. Only the value who's key matches keyName will be encoded by the method.
        inProcessPacket -- whatever has already been processed. Only used by post-processing tokens like length and checksums. 
        templateName -- the name of the calling template, used for debugging.
        """
        if self.keyName in encodeDict:  # keyName has a matching value in the encodeDict, proceed!
            return self._encode_(encodeDict[self.keyName], inProcessPacket) # call the subclass's _encode_ method for token-specific processing.
        elif self.requireEncodeDict: # no keyName has been found and dictionary required, so compose a useful error message and raise an exception.
            if templateName: errorMessage = str(self.keyName) + " not found in template " + templateName + "."
            else: errorMessage = str(self.keyName) + " not found in template."
            raise KeyError(errorMessage)
        else: return self._encode_(None, inProcessPacket)   #some tokens don't require an entry in the encode dictionary



#---- TOKEN TYPES ----

class unsignedInt(packetToken):
    """An unsigned integer token type."""
    
    def init(self, size = 1):
        """Initializes the unsigned integer token.
        
        size -- the length in bytes of the unsigned integer.
        """
        self.size = size # length of unsigned integer
    
    def _encode_(self, encodeValue, inProcessPacket):
        """Converts an unsigned integer into a sequence of bytes.
        
        encodeValue -- contains an unsigned integer.
        """
        return utilities.unsignedIntegerToBytes(encodeValue, self.size)


class length(packetToken):
    """A length-of-packet integer token type."""
    def init(self, size = 1, countSelf = False):
        """Initializes the length token.
        
        size -- the length in bytes of the token
        countSelf -- if true, the length byte will be counted
        """
        self.size = size
        self.countSelf = countSelf
        self.requireEncodeDict = False  #does not require an encode dictionary, because input is the entire in-process packet
    
    def _encode_(self, encodeValue, inProcessPacket):
        """Returns the length of the inProcessPacket, either including or nor itself.
        
        inProcessPacket -- contains a second-pass in-process packet whose length should be measured.
        
        NOTE: This assumes that there are not multiple length tokens in a single packet.
        """
        
        if len(inProcessPacket)>0:  #an inProcess packet has been provided
            #create and count a list only containing integers from the flattened inProcessPacket
            length = len(list(itertools.ifilter(lambda token: type(token) == int, utilities.flattenList(inProcessPacket))))
            if self.countSelf: length += 1
            return utilities.unsignedIntegerToBytes(length, self.size)  #convert to integer of lenth self.size
        else: return self   #no in-process packet has been provided.
        
        

class checksum(packetToken):
    """Performs a checksum operation on the in-process packet."""
    def init(self, polynomial = 7):
        """Initializes the checksum token.
        
        polynomial -- defines the taps used to generate a CRC value. For Gestalt, this defaults to 7 (ATM standard)
        """
        self.CRCInstance = utilities.CRC(polynomial)    # initialize a CRC gen/test class
        self.requireEncodeDict = False  #doesn't need an input from the encode dictionary
    
    def _encode_(self, encodeValue, inProcessPacket):
        """Returns the checksum value of the in-process packet.
        
        inProcessPacket -- contains a third-pass in-process packet whose checksum should be computed.
        """
        
        if len(inProcessPacket)>0: #an inProcess packet has been provided
            # create list of all the ints. At this point that should be everything but the checksum token
            checksumList = list(itertools.ifilter(lambda token: type(token) == int, utilities.flattenList(inProcessPacket)))
            return self.CRCInstance.generate(checksumList)  #generate and return checksum
        else: return self
        
class pList(packetToken):
    """A list-type token.
    
    Note that no length is provided, and whatever list is provided will be passed thru.
    """
    def _encode_(self, encodeValue, inProcessPacket):
        """Inserts the list provided in encodeValue into the packet.
        
        encodeValue -- contains the list to be inserted.
        """
        return encodeValue

class pString(packetToken):
    """A string-type token.
    
    Note that no length is provided, and whatever string is provided will be converted to a list and passed thru.
    """
    def _encode_(self, encodeValue, inProcessPacket):
        """Converts string into a list.
        
        encodeValue -- contains the string to be converted and inserted.
        """
        return utilities.stringToList(encodeValue)

class packet(packetToken):
    """An embedded packet.
    
    Note that this is similar to the pList token except that it converts a packet into a list on encode.
    The primary reason for breaking out out is to make embedded packets more explicit in the template definition.
    """
    def _encode_(self, encodeValue, inProcessPacket):
        """Converts sub-packet to list, and insert into packet.
        
        encodeValue -- contains a packets.packet instance.
        """
        return list(encodeValue)


class packetTemplate(packetToken):
    """A nested packet template.
    
    The primary use of this token type is to extend a packet definition.
    """
    
    def init(self, template):
        """Initializes packet template token.
        
        template -- a packets.template instance.
        """
        self.template = template
    
    def _encode_(self, encodeValue, inProcessPacket):
        """Encodes the nested packet template using the provided encoding dictionary.
        
        encodeValue -- contains the encoding dictionary to be encoded by the template.
        """
        
        return self.template.encode(encodeValue)


class signedInt(packetToken):
    """A signed integer token."""
    pass

class fixedPoint(packetToken):
    """A fixed point decimal token."""
    pass

