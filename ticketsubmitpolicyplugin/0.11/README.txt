= control ticket submission policy based on field information =

== Description ==

The TicketSubmitPolicyPlugin allows control of ticket submission based on fields and their values.  Actions are configurable via an extension point, ITicketSubmitPolicy.  Javascript is used to enforce the policy without leaving the page.

Each policy has a condition, which controls when the policy is
applied, and actions that are applied when the condition is met.

The condition is in the form of "field" "comparitor" "field value".
The field is a field of the ticket (e.g. 'type'), 
the field value is its value (e.g. 'defect'),
the comparitor is some
rule that is applied to the field and its value (e.g. 'is not').

The following comparitors have been implemented:

 * is 
 * is not
 * is in : the field is one of a list
 * is not in

This should probably become an extension point so that these are
easily pluggable.

''"is in" and 'is not in' have NOT been tested are PROBABLY CONTAIN
BUGS!  only use these if you want to test them or can contribute
debugging data regarding them''

Policy actions are an ExtensionPoint of components fulfilling the
ITicketSubmitPolicy interface.  Bundled with the
TicketSubmitPolicyPlugin are two such actions:

* requires : require fields before allowing form submission

* excludes : exclude fields from form display and submission

Each of these, and currently actions in general, take multiple
arguments in the form of ticket fields.

== Example ==

The following section in trac.ini excludes the version field excludes the version field if the type is not a defect and requires a version that is not blank if the type is a defect:

{{{
[ticket-submit-policy]
policy1.condition = type is not defect
policy1.excludes = version
policy2.condition = type is defect
policy2.requires = version
}}}

{{{&&}}}s may be used to join multiple conditions together, and
multiple arguments may be supplied to requires and excludes as well:

{{{
[ticket-submit-policy]
policy1.condition = type is defect && component is not component2
policy1.requires = version, milestone
policy2.condition = type is not defect
policy2.excludes = version, priority
}}}
