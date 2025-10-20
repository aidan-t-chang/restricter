edgeXml = """
<AppLockerPolicy Version="1">
    <RuleCollection Type="Appx" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Dll" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Exe" EnforcementMode="NotConfigured">
        <FilePublisherRule Id="43065e5f-4025-43db-a021-a31867446c92" Name="MICROSOFT EDGE, from O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" Description="" UserOrGroupSid="S-1-1-0" Action="Deny">
            <Conditions>
                <FilePublisherCondition PublisherName="O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" ProductName="MICROSOFT EDGE" BinaryName="MSEDGE.EXE">
                    <BinaryVersionRange LowSection="*" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
    </RuleCollection>
    <RuleCollection Type="Msi" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Script" EnforcementMode="NotConfigured"/>
</AppLockerPolicy>
"""

enabledDefaultsXml = """
<AppLockerPolicy Version="1">
    <RuleCollection Type="Exe" EnforcementMode="NotConfigured">
        <FilePublisherRule Id="46652a30-5fad-467d-9950-b73c36c60327" Name="Signed by O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePublisherCondition PublisherName="O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" ProductName="*" BinaryName="*">
                    <BinaryVersionRange LowSection="*" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
        <FilePublisherRule Id="6206f54d-9c04-4edf-9c11-0b316f8a3d08" Name="MICROSOFT® WINDOWS® OPERATING SYSTEM, from O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePublisherCondition PublisherName="O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" ProductName="MICROSOFT® WINDOWS® OPERATING SYSTEM" BinaryName="*">
                    <BinaryVersionRange LowSection="*" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
        <FilePathRule Id="8ce8c67f-cc8a-4c9b-9a97-9a1003d523c0" Name="%SYSTEM32%\*" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePathCondition Path="%SYSTEM32%\*"/>
            </Conditions>
        </FilePathRule>
        <FilePathRule Id="ad051e01-8fed-4125-83a1-b34d805ccdc9" Name="%WINDIR%\*" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePathCondition Path="%WINDIR%\*"/>
            </Conditions>
        </FilePathRule>
        <FilePathRule Id="c0dc9913-0ece-468d-930f-e17350f370c7" Name="%PROGRAMFILES%\Google\*" Description="" UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePathCondition Path="%PROGRAMFILES%\Google\*"/>
            </Conditions>
        </FilePathRule>
        <FilePathRule Id="c2a197c1-e462-4071-920b-cdb8001be0f9" Name="%PROGRAMFILES%\Microsoft\Edge\*" Description="" UserOrGroupSid="S-1-1-0" Action="Deny">
            <Conditions>
                <FilePathCondition Path="%PROGRAMFILES%\Microsoft\Edge\*"/>
            </Conditions>
        </FilePathRule>
    </RuleCollection>
    <RuleCollection Type="Msi" EnforcementMode="NotConfigured">
        <FilePathRule Id="b9af7461-1b0e-41b1-bce5-42b50efeeb23" Name="*" Description="" UserOrGroupSid="S-1-1-0" Action="Deny">
            <Conditions>
                <FilePathCondition Path="*"/>
            </Conditions>
        </FilePathRule>
    </RuleCollection>
    <RuleCollection Type="Script" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Dll" EnforcementMode="NotConfigured"/>
    <RuleCollection Type="Appx" EnforcementMode="NotConfigured">
        <FilePublisherRule Id="a9e18c21-ff8f-43cf-b9fc-db40eed693ba" Name="(Default Rule) All signed packaged apps" Description="Allows members of the Everyone group to run packaged apps that are signed." UserOrGroupSid="S-1-1-0" Action="Allow">
            <Conditions>
                <FilePublisherCondition PublisherName="*" ProductName="*" BinaryName="*">
                    <BinaryVersionRange LowSection="0.0.0.0" HighSection="*"/>
                </FilePublisherCondition>
            </Conditions>
        </FilePublisherRule>
    </RuleCollection>
</AppLockerPolicy>
"""