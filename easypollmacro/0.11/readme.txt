Installations Instructions
---------------------------
Please refer to this link for EasyPoll Macro installation
http://trac.edgewall.org/wiki/TracPlugins

Requirements(IMPORTANT):
-------------------------
1. EasyPoll is db driven poll macro, to make it work you have to have easypoll table in your Trac database. easypoll.sql can be found in db updates folder.
2. EASYPOLL_CREATE : User who has EASYPOLL_CREATE or TRAC_ADMIN permission can create easy polls in wiki or ticket page.
3. EASYPOLL_VOTE : User who has EASYPOLL_VOTE or TRAC_ADMIN permission can vote on easy polls in wiki or ticket page.

EasyPoll: Fully featured Database driven poll plugin with permission controlls for voting and poll creation. Google charts for showing poll results.
        Description: The purpose of this plugin is to provide an easy way to integrate polls in Trac wiki and ticket pages.
        Easy poll uses mysql db for storing poll related data and uses google charts to show results of polls.
        Features:
        1. Response type: You can decide the response type for polls i.e whether you want single response poll(radio button poll) or multiple response poll(checkbox button poll).
        2. Google charts type: You can decide which type of chart you want to use for showing results.
        3. Poll options: Poll option can be any valid english string or any Ticket number(EasyPoll will fetch summary for ticket id given and use as a option text).
        4. Change vote: You can manage whether user can change their vote or not.
        
        Sample Example:
        ------------------------------------------------------------------------
        
        [[EasyPoll( name = my first poll,
                    title = What's your favorite programming language?,
                    response_type = single,
                    options = Python : PHP : JAVA : C : Lisp,
                    user_can_change_vote = false,
                    chart_type = pie
                   )
        ]]
        
        Attributes explanation:
        ------------------------------------------------------------------------
        1. name(required) : name is used as a poll identifier, if you change the name value than it will be treated as new poll.
        Nowhere in the poll the name will be shown. Don't change the name of the poll after poll creation
        2. title(required) : title will be used as a poll title. You can change it whenever you want. Each time the existing poll will be updated.
        3. options(required) : options should be separated by colon (:)
            option can also have Ticket id as their option like
            options = #1 : #2 : #3 In this case the summary will be pulled out from the valid tickets and will be used as option text with ticket link.
        4. response(optional) : reponse can take two values (i) multiple and (ii) single. Default is (ii)single option
            (i) multiple : multiple response type will generate poll with checkboxes, in this case user can choose multiple options.
            (ii) single : single reponse type will generate poll with radio buttons, in this case user can choose only one option
        5. user_can_change_vote(optional) : user_can_change_vote can take two values (i) false and (ii) true. Default is false
            (i) false : once user cast their vote, they cannot change their vote, Poll will be disabled for them, however they can see poll results.
            (ii) true : user can change their vote anytime and many times. Poll will always be enabled for them and they can see poll results.
        6. chart_type(optional) : chart_type can take two values (i) pie and (ii) bar. Default is pie.
            (i) pie : Pie chart will be used to show poll results.
            (ii) bar : Bar chart will be used to show poll results.
            User can see poll results only after casting their vote.
            
        Permissions Explanation:
        ------------------------------------------------------------------------
        1. EASYPOLL_CREATE : User who has EASYPOLL_CREATE or TRAC_ADMIN permission can create easy polls in wiki or ticket page.
        2. EASYPOLL_VOTE : User who has EASYPOLL_VOTE or TRAC_ADMIN permission can vote on easy polls in wiki or ticket page.
        
        Every login user on Trac can see EasyPoll but can vote or create only if user has sufficient permissions.
        
        Limitations:
        ------------------------------------------------------------------------
        1. As of now only supports ascii characters.
        2. Don't use comma(,) while picking easy poll attributes. By design comma(,) is used as a attribute separator
        

