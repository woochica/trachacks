= control ticket submission policy based on field information =

== Description ==

The TicketSubmitPolicyPlugin allows control of ticket submission based on fields and their values.  Actions are configurable via an extension point, ITicketSubmitPolicy.  Javascript is used to enforce the policy without leaving the page.

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
