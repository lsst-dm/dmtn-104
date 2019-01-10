#!/usr/bin/env python
# connect to magicDraw 
# and get model information

import requests
from base64 import b64encode

# Subsystem  Design Workspace @ID
sdw = '3130d49c-d90d-4df2-a110-5247a5d03296'
dms = '698d501b-660d-4d7e-8875-c6170ca0f513'
trunk = '698d501b-660d-4d7e-8875-c6170ca0f513'
dmpl = 'a0acbaa6-6625-4ea9-8aec-51931412a29e' # DM Problem/Logic element server id
dmcmp = '60706435-6f8e-4b15-823b-06597f1cdada' # DM Components element server ID
connectionId = b64encode(b"gcomoretto-read:dm-read").decode("ascii")
#print(connectionId)

headers = {
    'accept': 'application/json',
    'authorization': 'Basic %s' % connectionId
}

# here a copuple of interesting examples
# https://stackoverflow.com/questions/12737740/python-requests-and-persistent-sessions
# https://stackoverflow.com/questions/2594880/using-curl-with-a-username-and-password


def getelement(eid):
# response[0]
#   ldp:membershipResource
#   @type
#   ldp:contains
#   ldp:hasMemberRelation
#   @id
#   @context
# response[1]
#   kerml:name
#   @base
#   kerml:nsURI
#   @type
#   kerml:owner
#   kerml:revision
#   @context
#   kerml:ownedElement
#   kerml:modifiedTime
#   kerml:esiData
#   kerml:resource
#   kerml:esiID
#   @id
# response[1]['kerml:esiData']['packagedElement']
#   _directedRelationshipOfSource
#   _classifierOfInheritedMember
#   _representationText
#   ownedRule
#   packagedElement
#   packageMerge
#   ownedTemplateSignature
#   _considerIgnoreFragmentOfMessage
#   _elementOfSyncElement
#   _packageImportOfImportedPackage
#   _namespaceOfMember
#   ID
#   _relationshipOfRelatedElement
#   nameExpression
#   owningTemplateParameter
#   _manifestationOfUtilizedElement
#   _durationObservationOfEvent
#   visibility
#   _messageOfSignature
#   _templateParameterSubstitutionOfOwnedActual
#   _componentOfPackagedElement
#   _constraintOfConstrainedElement
#   _namespaceOfImportedMember
#   clientDependency
#   _diagramOfContext
#   nestedPackage
#   ownedType
#   name
#   _directedRelationshipOfTarget
#   elementImport
#   _commentOfAnnotatedElement
#   ownedMember
#   supplierDependency
#   _informationFlowOfInformationTarget
#   ownedComment
#   _timeObservationOfEvent
#   _packageMergeOfMergedPackage
#   _informationFlowOfInformationSource
#   URI
#   _templateParameterOfOwnedDefault
#   templateParameter
#   member
#   ownedDiagram
#   _templateParameterOfDefault
#   owner
#   profileApplication
#   ownedElement
#   visibility__from_PackageableElement
#   packageImport
#   syncElement
#   _activityPartitionOfRepresents
#   _elementValueOfElement
#   owningPackage
#   nestingPackage
#   templateBinding
#   namespace
#   ownedStereotype
#   importedMember
#   mdExtensions
#   appliedStereotypeInstance
#   _templateParameterSubstitutionOfActual
#   _elementImportOfImportedElement


def reqget(url, headers):
    result = requests.get(url,headers=headers, verify=False).json()
    return(result)

s = requests.Session()

r = s.get('https://twcloud.lsst.org:8111/osmc/login', headers=headers, verify=False)
#print(s.cookies)
#print(s)
if r.status_code == 401:
    print('Connectino error')
    exit()

#response = requests.get('https://twcloud.lsst.org:8111/osmc/workspaces/'+sdw+'/resources/'+dms+'/artifacts', headers=headers, verify=False).json()
#response = requests.get('https://twcloud.lsst.org:8111/osmc/resources/'+dms+'/artifacts', headers=headers, verify=False).json()
#for el in response:
#    print('  ...  ', el, ' ...')
#    print(response[el])

#artifacts = response['ldp:contains']

url = 'https://twcloud.lsst.org:8111/osmc/resources/' + dms + '/elements/' + dmcmp
response = reqget(url, headers)
#print(response)

print(response[1]['kerml:esiData']['name'])
count = 0
for el in response[1]['kerml:esiData']['packagedElement']:
    print('  ..  ', el)

for el in response:
    print(count)
    for e in el:
#   print('    ..  ', e)
##   print('    ..  ', e, '  -  ', el[e])
#    count = count + 1
print()

for el in response[1]['kerml:esiData'].keys():
    print('   ..  ', el)


#for a in artifacts:
    #count = count + 1
    #print("- ", count, ': ', a)
    #r2 = requests.get('https://twcloud.lsst.org:8111/osmc/workspaces/'+sdw+'/resources/'+dms+'/artifacts/'+a, headers=headers, verify=False).json()
    #r2 = requests.get('https://twcloud.lsst.org:8111/osmc/resources/'+dms+'/elements/'+a, headers=headers, verify=False).json()
    #print(r2)
    #print(r2[1]['author'])
    #print(r2[1]['resourceID'])
    #print(r2[1]['dcterms:title'])
    #for el in r2:
#   #print(el.keys())
#   #print("  . ", el)
#   #print("  . ", el, ' -- ', r2[el])
#   #for e in el.keys():
#   #    print('  .. ', e,' - ' , el[e])
    #print()
#
#print(response[0]['ldp:contains'])

#print('Found ', count, 'artifacts')
