
from XSConsoleBases import *
import XenAPI

class Auth:
    loggedInName = 'root'
    loggedInPassword = 'xenroot'
    error = ""
    
    @classmethod
    def LoggedInUsername(cls):
        return cls.loggedInName

    @classmethod
    def LoggedInPassword(cls):
        return cls.loggedInPassword
 
    @classmethod
    def ErrorMessage(cls):
        return cls.error
    
    @classmethod
    def ProcessLogin(cls, inUsername, inPassword):
        # Just accept anything
        cls.loggedInName = inUsername
        cls.loggedInPassword = inPassword
        
        session = cls.OpenSession()
        if session is None:
            cls.loggedInName = None
            cls.loggedInPassword = None
            retVal = False
        else:
            cls.CloseSession(session)
            retVal = True
        return retVal
        
    @classmethod
    def IsLoggedIn(cls):
        return cls.loggedInName != None
        
    @classmethod
    def LogOut(cls):
        cls.loggedInName = None

    @classmethod
    def OpenSession(cls):
        session = None
        if (Auth.LoggedInUsername() != None and Auth.LoggedInPassword() != None):
            session = XenAPI.Session("http://127.0.0.1")
            try:
                session.login_with_password(cls.LoggedInUsername(), cls.LoggedInPassword())
            except Exception, e:
                session = None
                cls.error = str(e)
        
        return session
        
    @classmethod
    def CloseSession(cls, inSession):
        pass