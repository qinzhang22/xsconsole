# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
import xml.dom.minidom

class SRNewDialogue(Dialogue):
    srTypeNames = {
        'NFS': Lang('NFS Storage'),
        'ISCSI': Lang('iSCSI Storage'),
        'NETAPP': Lang('NetApp'),
        'CIFS_ISO': Lang('Windows File Sharing (CIFS) ISO Library'),
        'NFS_ISO': Lang('NFS ISO Library')
    }    
    
    def __init__(self, inVariant):

        Dialogue.__init__(self)
        self.variant = inVariant
        self.srParams = {}
        self.createMenu = Menu()

        choices = ['NFS']
        #choices = ['NFS', 'ISCSI', 'NETAPP', 'CIFS_ISO', 'NFS_ISO']
        for type in choices:
            self.createMenu.AddChoice(name = self.srTypeNames[type],
                onAction = self.HandleCreateChoice,
                handle = type)
                
        
        self.ChangeState('INITIAL')
    
    def BuildPanePROBE_NFS(self):
        self.srMenu = Menu()
        for srChoice in self.srChoices:
            self.srMenu.AddChoice(name = srChoice,
            onAction = self.HandleProbeChoice,
            handle = srChoice)
        if self.srMenu.NumChoices() == 0:
            self.srMenu.AddChoice(name = Lang('<No Storage Repositories Present>'))
            
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("New Storage Repository"))
        pane.AddBox()
        if hasattr(self, 'BuildPane'+self.state):
            handled = getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
            
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please select the type of Storage Repository to ')+Lang(self.variant.lower()))
        pane.AddMenuField(self.createMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsGATHER_NFS(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Please enter a name and path for the NFS Storage Repository'))
        pane.AddInputField(Lang('Name', 16), self.srParams.get('name', Lang('NFS Virtual Disk Storage')), 'name')
        pane.AddInputField(Lang('Description', 16), '', 'description')
        pane.AddInputField(Lang('Share Name', 16), self.srParams.get('sharename', 'server:/path'), 'sharename')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsPROBE_NFS(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField('WARNING')
        pane.AddWrappedBoldTextField(Lang('You must ensure that the chosen SR is not in use by any server '
            'that is not a member of this Pool.  Failure to do so may result in data loss.'))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang('Please select the Storage Repository to ')+Lang(self.variant.lower()))
        pane.NewLine()

        pane.AddMenuField(self.srMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddTitleField(Lang('Press <F8> to ')+Lang(self.variant.lower())+Lang(' this Storage Repository'))
        
        pane.AddStatusField(Lang('SR Type', 16), self.srTypeNames[self.createType])
        for name, value in self.extraInfo:
            pane.AddStatusField(name.ljust(16, ' '), value)
        
        pane.NewLine()

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyINITIAL(self, inKey):
        return self.createMenu.HandleKey(inKey)

    def HandleKeyGATHER_NFS(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            if pane.IsLastInput():
                try:
                    inputValues = pane.GetFieldValues()
                    if self.variant == 'ATTACH':
                        Layout.Inst().TransientBanner(Lang('Probing for Storage Repositories...'))
                    self.HandleNFSData(inputValues)
                except Exception, e:
                    pane.InputIndexSet(None)
                    Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
            else:
                pane.ActivateNextInput()
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyPROBE_NFS(self, inKey):
        return self.srMenu.HandleKey(inKey)

    def HandleKeyCONFIRM(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            try:
                getattr(self, 'Commit'+self.variant)() # Despatch method named 'Commit'+self.variant
            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Operation Failed"), Lang(e)))
            handled = True
        return handled

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey in ('KEY_ESCAPE', 'KEY_LEFT'):
            Layout.Inst().PopDialogue()
            handled = True

        return handled
    
    def HandleCreateChoice(self, inChoice):
        self.createType = inChoice
        
        self.ChangeState('GATHER_'+inChoice)

    def HandleProbeChoice(self, inChoice):
        self.srParams['uuid'] = inChoice
        self.extraInfo.append( (Lang('SR ID'), inChoice) ) # Append tuple, so double brackets
        self.ChangeState('CONFIRM')

    def HandleNFSData(self, inParams):
        self.srParams = inParams
        match = re.match(r'([^:]*):([^:]*)$', self.srParams['sharename'])
        if not match:
            raise Exception(Lang('Share name must contain a single colon, e.g. server:/path'))
        self.srParams['server'] = IPUtils.AssertValidNetworkName(match.group(1))
        self.srParams['serverpath'] = IPUtils.AssertValidNFSPathName(match.group(2))
        self.extraInfo = [ # Array of tuples
            (Lang('Name'), self.srParams['name']),
            (Lang('Share Name'), self.srParams['sharename'])
            ]

        if self.variant == 'CREATE':
            self.ChangeState('CONFIRM')
        elif self.variant == 'ATTACH':
            xmlSRList = Task.Sync(lambda x: x.xenapi.SR.probe(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                { # device_config
                    'server':self.srParams['server'],
                    'serverpath':self.srParams['serverpath'],
                },
                'nfs' # type
                )
            )
            # Parse XML for UUID values
            xmlDoc = xml.dom.minidom.parseString(xmlSRList)
            self.srChoices = [ node.firstChild.nodeValue.strip() for node in xmlDoc.getElementsByTagName("UUID") ]
                
            self.ChangeState('PROBE_NFS')
        else:
            raise Exception('Bad self.variant') # Logic error
            
    def CommitCREATE(self):
        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang('Creating SR...'))
        try:
            Task.Sync(lambda x: x.xenapi.SR.create(
                HotAccessor().local_host_ref().OpaqueRef(), # host
                { # device_config
                    'server':self.srParams['server'],
                    'serverpath':self.srParams['serverpath'],
                },
                '0', # physical_size
                self.srParams['name'], # name_label
                self.srParams['description'], # name_description
                'nfs', # type
                'user', # content_type
                True # shared
                )
            )
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Creation Successful")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Creation Failed"), Lang(e)))

    def CommitATTACH(self):
        for sr in HotAccessor().sr:
            if sr.uuid() == self.srParams['uuid']:
                raise Exception(Lang('SR ID ')+self.srParams['uuid']+Lang(" is already attached to the system as '")+sr.name_label(Lang('<Unknown>'))+"'")

        Layout.Inst().PopDialogue()
        Layout.Inst().TransientBanner(Lang('Attaching Storage Repository...'))
        srRef = None
        pbdList = []
        pluggedPBDList = []
        try:
            srRef = Task.Sync(lambda x: x.xenapi.SR.introduce(
                self.srParams['uuid'], # uuid
                self.srParams['name'], # name_label
                self.srParams['description'], # name_description
                'nfs', # type
                'user', # content_type
                True # shared
                )
            )

            for host in HotAccessor().host:
                pbdList.append(Task.Sync(lambda x: x.xenapi.PBD.create({
                    'host':host.HotOpaqueRef().OpaqueRef(), # Host ref
                    'SR':srRef, # SR ref
                    'device_config':{ # device_config
                        'server':self.srParams['server'],
                        'serverpath':self.srParams['serverpath'],
                    }
                })))
            
            for pbd in pbdList:
                Task.Sync(lambda x: x.xenapi.PBD.plug(pbd))
                pluggedPBDList.append(pbd)
                
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Attachment Successful")))

        except Exception, e:
            message = Lang(e)
            # Attempt to undo the work we've done, because the SR is incomplete
            try:
                for pluggedPBD in pluggedPBDList:
                    Task.Sync(lambda x: x.xenapi.PBD.unplug(pluggedPBD))
                for pbd in pbdList:
                    Task.Sync(lambda x: x.xenapi.PBD.destroy(pbd))
                    
                Task.Sync(lambda x: x.xenapi.SR.forget(srRef))
                
            except Exception, e:
                message += Lang('.  Attempts to rollback also failed: ')+Lang(e)

            Layout.Inst().PushDialogue(InfoDialogue(Lang("Storage Repository Attachment Failed"), message))

class XSFeatureSRCreate:
    @classmethod
    def CreateStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Create New Storage Repository"))
    
        inPane.AddWrappedTextField(Lang(
            "This option is used to create a new Storage Repository."))
    
    @classmethod
    def AttachStatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Attach Existing Storage Repository"))
    
        inPane.AddWrappedTextField(Lang(
            "This option is used to attach a Storage Repository or ISO library that already exists."))
    
    @classmethod
    def CreateActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SRNewDialogue('CREATE')))
    
    @classmethod
    def AttachActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SRNewDialogue('ATTACH')))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SR_CREATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 50,
                'menutext' : Lang('Create New Storage Repository') ,
                'statusupdatehandler' : self.CreateStatusUpdateHandler,
                'activatehandler' : self.CreateActivateHandler
            }
        )

        Importer.RegisterNamedPlugIn(
            self,
            'SR_ATTACH', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 40,
                'menutext' : Lang('Attach Existing Storage Repository') ,
                'statusupdatehandler' : self.AttachStatusUpdateHandler,
                'activatehandler' : self.AttachActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSRCreate().Register()