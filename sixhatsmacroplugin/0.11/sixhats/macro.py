""" Sixhats plugin for Trac.
    
    This is a cosmetic plugin, it only makes pretty headings.
"""
import re
from urlparse import urlparse
from genshi.builder import tag
from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.macros import WikiMacroBase
from trac.ticket.query import Query


SIZES = {
    'fedora': {
        's': (52, 39),  #  50 %
        'm': (78, 59),  #  75 %
        'l': (105, 79), # 100 %
    },
    
    'hardhat': {
        's': (57, 39),
        'm': (86, 59),
        'l': (115, 79),
    },

    'tophat': {
        's': (43, 39),
        'm': (64, 59),
        'l': (85, 79),
    }
}

TITLES = {
    'white': 'Information, Facts and Figures',
    'red': 'Feelings, Emotions and Intuition',
    'black': 'Critical, Cautious and Careful',
    'yellow': 'Constructive, Benefits and Values',
    'green': 'Creative, New and Improved',
    'blue': 'Overview and Guidance'
}


HELP = '''\
[[Sixhats(blue)]] # Blue hat, default size and description.
[[Sixhats(red,size=m,type=fedora)]] # Medium hat, type fedora.
[[Sixhats(black,Find all the problems\, issues with this idea,type=hardhat,size=40%,h=1)]] # Custom size, <h1> heading.
'''

def get_absolute_url(base, url):
    """ Generate an absolute url from the url with the special schemes
        {htdocs,chrome,ticket,wiki,source} simply return the url if given with
        {http,https,ftp} schemes.
        
        Examples:
            http://example.com/filename.ext
                ie. http://www.google.com/logo.jpg
            
            chrome://site/filename.ext
            htdocs://img/filename.ext
                note: `chrome` is an alias for `htdocs`
            
            ticket://number/attachment.pdf
                ie. ticket://123/specification.pdf
            
            wiki://WikiWord/attachment.jpg
            
            source://changeset/path/filename.ext
                ie. source://1024/trunk/docs/README
    """
    def ujoin(*parts):
        """ Remove double slashes.
        """
        parts = [part.strip('/') for part in parts]
        return '/' + '/'.join(parts)
    
    scheme, netloc, path, query, params, fragment = urlparse(url)
    
    if scheme in ('ftp', 'http', 'https'):
        return url
    
    if scheme in ('htdocs', 'chrome'):
        return ujoin(base, 'chrome', path)
    
    if scheme in ('source',):
        return ujoin(base, 'export', path)
    
    if scheme in ('ticket',):
        return ujoin(base, 'raw-attachment/ticket', path)
    
    if scheme in ('wiki',):
        return ujoin(base, 'raw-attachment/wiki', path)
    
    return url

def squish_string(s):
    """ Generate a string suitable for anchor tags.
    """
    def cap(s):
        """ s.title()/string.capitalize() lowers internal caps.
        """
        if len(s) >= 2:
            return s[0].upper() + s[1:]
        else:
            return s
    
    return ''.join(cap(i) for i in re.split(r'[\s\^\+\=.,/?;:\'"\[\]{}\|\\!@#$%^&*()_-]', s))

def string_keys(d):
    """ Convert unicode keys into string keys, suiable for func(**d) use.
    """
    sdict = {}
    for key, value in d.items():
        sdict[str(key)] = value
    
    return sdict


class SixhatsMacro(WikiMacroBase):
    
    implements(IWikiMacroProvider, ITemplateProvider)
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content, strict=False)
        
        if len(args) == 1:
            hat = args[0].lower()
            title = TITLES.get(hat, '')
        
        elif len(args) == 2:
            hat = args[0].lower()
            title = args[1]
        
        # An simple Exception would probabl;y be better, see http://../ for examples.
        if len(args) == 0 or hat not in ('black', 'blue', 'green', 'red', 'white', 'yellow', 'intro', 'cite'):
            raise TracError('Invalid parameters, see http://trac-hacks.org/wiki/SixhatsMacro#Examples for example uses.')
            #tags = [tag.strong()('Error: Invalid parameters, see the following examples:')]
            #tags.extend([tag.pre()(i) for i in HELP.splitlines()])
            #return tag.div(class_='system-message')(*tags)
        
        if hat == 'cite':
            if not title:
                title = "The best way to learn the Six Hats method is to read Edward de Bono's "
            url = get_absolute_url(formatter.href.base, 'htdocs://sixhats/pdf/six_thinking_hats.pdf')
            return tag.p()(title, tag.a(href=url)('Six Thinking Hats'), '.')
        
        # Not too sure if a plugin should be self-documenting.
        if hat == 'intro':
            hide = kwargs.get('hide')
            
            tags = []
            tags.append(tag.h1(id='SixHatsIntroduction')('Six Hats Introduction'))
            tags.append(tag.blockquote(tag.p("There is nothing more sad and wasteful than a roomful of intelligent and highly paid people waiting for a chance to attack something the speaker has said. With the Six Hats method the fullest use is made of everyone's intelligence, experience and information. The Six Hats also removes all 'ego' from the discussion process.")))
            tags.append(tag.p('The Six Thinking Hats represent directions of thought. They are used to request thinking in a paticular direction, ', tag.strong('not'), ' as a description or label to classify your thinking afterwards. They are ', tag.strong('not'), ' used to characterize people. A person is not a black hat, but he or she might prefer to think with the black hat on. It is desirable for everyone to become skilled in the use of all the hats.'))
            tags.append(self.expand_macro(formatter, name, 'cite'))
            tags.append(tag.h1(id='Summary')('Summary'))
            tags.append(self.expand_macro(formatter, name, 'white,size=m'))
            
            li = [
                tag.li('The white hat is neutral and objective.'),
                tag.li('It focusses on facts and figures.'),
            ]
            
            sub_li = [ 
                tag.li('What information do we have?'),
                tag.li('What information do we need?'),
                tag.li('What information is missing?'),
                tag.li('What questions do we need to ask?'),
                tag.li('How are we going to get the information we need?')
            ]
            
            li.append(tag.li('Questions to ask with the white hat on:', tag.ul(*sub_li)))
            li.extend([
                tag.li('The information can range from hard verifiable facts and figures to soft information such as 3rd party opinions and feelings. Your own opinions and feelings are placed under the red hat.'),
                tag.li('Whose fact is it?'),
                tag.li('Is the information a fact, a likelyhood or a believe?')
            ])
            
            sub_li = [
                tag.li('Always true'),
                tag.li('Usually true'),
                tag.li('Generally true'),
                tag.li('By and large'),
                tag.li('More often than not'),
                tag.li('About half the time'),
                tag.li('Often'),
                tag.li('Sometimes true'),
                tag.li('Occastionally true'),
                tag.li('Been known to happen'),
                tag.li('Never true'),
                tag.li('Cannot be true (contradictory)')
            ]
            
            li.append(tag.li('How true is the fact? Frame the information appropriatly:', tag.ul(*sub_li)))
            li.append(tag.li('Split the facts into two groups: checked facts and believed facts.'))
            tags.append(tag.ul(*li))
            
            tags.append(self.expand_macro(formatter, name, 'red,size=m'))
            
            li = [
                tag.li('The red hat is subjective and generally non-rational.'),
                tag.li('It exposes and legitimizes emotions and feelings.'),
                tag.li('It allows people to express their opinions, hunches, intuitions and impressions. (a function of their experience)'),
                tag.li("Resist the temptation to justify your emotions. You don't need to give a reason or a logical basis."),
                tag.li('If emotions and feelings are not permitted as inputs in the thinking process, they will lurk in the background and affect all the thinking in a hidden way.'),
                tag.li('The red hat makes feelings visible so that they can become part of the thinking map and also part of the value system that chooses the route on the map.')
            ]
            
            sub_li = [
                tag.li('Ordinary emotions such as fear and dislike to more subtle ones such as suspicion.'),
                tag.li('Complex judgements that go into such type of feelings as a hunch, intuition, sense, taste, aesthetic feeling and other not visibly justified types of feeling.')
            ]
            
            li.append(tag.li('The red hat covers two broad types of feelings:', tag.ol(*sub_li)))
            tags.append(tag.ul(*li))
            
            tags.append(self.expand_macro(formatter, name, 'black,size=m'))
            
            li = [
                tag.li('The black hat is critical and logical (negative judgements).'),
                tag.li("It's perhaps the most important hat, the hat of survival, of caution and of being careful."),
                tag.li('It points out how something does not fit our experience, our resources, our policy, our stragegy, our ethics, our values, etc.'),
                tag.li('It protects us from wasting energy and money, it seeks to avoid dangers, problems, obstacles and difficulties.'),
                tag.li('There must be a logical basis for the criticism and reasons must be capable of standing on their own.'),
                tag.li('It focuses on why something may not work or may not be the right thing to do.'),
            ]
            
            sub_li = [ 
                tag.li('Be as causious and as fiercely critical as possible.'),
                tag.li('Point out errors or deficiencies in the thinking process.'),
                tag.li('Question the strength of the evidence.'),
                tag.li('What are the risks?'),
            ]
            
            li.append(tag.li('In order to get the full value from any suggestion or idea, it is important that the black hat be done thoroughly:', tag.ul(*sub_li)))
            li.extend([
                tag.li('Black hat thinking is not argument and must not be allowed to degenerate into argument.'),
                tag.li(tag.strong('Caution:'), ' There are people who overuse the black hat and who spend all their time trying to find fault. The fault is not in the black hat but in the abuse, overuse or misuse of the black hat.')
            ])
            
            tags.append(tag.ul(*li))
            
            tags.append(self.expand_macro(formatter, name, 'yellow,size=m'))
            
            li = [
                tag.li('The yellow hat is optimistic and logical (positive judgements).')
            ]
            
            sub_li = [ 
                tag.li('The generation of proposals.'),
                tag.li('The positive assessment of proposals.'),
                tag.li("Developing or 'building up' of proposals.")
            ]
            
            li.append(tag.li('The yellow hat is concerned with:', tag.ol(*sub_li)))
            li.extend([
                tag.li('Under the yellow hat a thinker deliberatly sets out to find whatever benefit there may be in a suggestion.'),
                tag.li('It is a waste of time setting out to be creative if you are not going to recognize a good idea.'),
                tag.li('Value and benefit are by no means always obvious.'),
                tag.li('Since the yellow hat is logical you should give a reason for the value you put forward.'),
                tag.li('The emphasis of yellow hat thinking is on exploration and positive speculation, oppertunity seeking.'),
                tag.li("Yellow hat thinking is concerned with the positive attitude of getting the job done, let's make it happen.")
            ])
            
            tags.append(tag.ul(*li))
            
            tags.append(self.expand_macro(formatter, name, 'green,size=m'))
            
            li = [
                tag.li('The green hat is creative, sometimes illogical.'),
                tag.li('The green hat is concerned with new ideas and new ways of looking at things, new perceptions.'),
                tag.li("Under the green hat we lay out options, alternatives and 'possibilities'."),
                tag.li('It corrects the faults found under the black hat and find noval ways the exploit the opportunities identified under the yellow hat.'),
                tag.li('You use the green hat to deliberately go after new ideas instead of waiting for them to come to you.'),
                tag.li('Sometimes you may be required to put forward provocations, illogical ideas, in order to provoke new concepts.'),
                tag.li('Under the green hat we use ideas as stepping stones, for their movement value, moving us to new ideas.'),
                tag.li('Use random words and ', tag.em('Po'), '.')
            ]
            
            tags.append(tag.ul(*li))
            
            tags.append(self.expand_macro(formatter, name, 'blue,size=m'))
            
            li = [
                tag.li('The blue hat is for meta-thinking, thinking about thinking.'),
                tag.li('Wearing the blue hat we are no longer thinking about the subject; instead, we are thinking about the thinking needed to explore the subject.'),
                tag.li('The blue hat thinker is like the conductor of an orchestra.'),
                tag.li("Generally the blue hat is worn by the facilitator, chairperson or leader of the session, it's a permanent role."),
                tag.li('The blue hat is for the organization and management of thinking, it also controls the process of thinking.'),
                tag.li('The initial blue hat defines the problem, list constraints and sets the agenda, the sequence of the other hats to be used.'),
                tag.li('Blue hat thinking stops arguments, enforces the discipline and keep people focussed on map making.'),
                tag.li('The final blue hat is responsible for summaries, overviews and conclusions.')
            ]
            
            tags.append(tag.ul(*li))
            
            fedoras = tag.a('fedoras', href=get_absolute_url(formatter.href.base, 'htdocs://sixhats/img/source/fedoras.svg'))
            hardhats = tag.a('hardhats', href=get_absolute_url(formatter.href.base, 'htdocs://sixhats/img/source/hardhats.svg'))
            tophats = tag.a('tophats', href=get_absolute_url(formatter.href.base, 'htdocs://sixhats/img/source/tophats.svg'))
            
            tags.append(tag.p('PS. If you wish to use any of these images in your own documents rather use the high quality vectors: ', fedoras, ', ', hardhats, ' and ', tophats, '.'))
            
            if hide:
                add_script(formatter.req, 'sixhats/js/hide.js')
                
                if hide.lower() == 'hide':
                    return ''.join([str(i) for i in ('- ', tag.a(id='hide', href='#', style='font-size: 8pt;')('show six hats introduction'), ' -', tag.div(id='introduction', style='display: none;', *tags))])
                else:
                    return ''.join([str(i) for i in ('- ', tag.a(id='hide', href='#', style='font-size: 8pt;')('hide six hats introduction'), ' -', tag.div(id='introduction', *tags))])
            else:
                return tag.div(id='introduction', *tags)
        
        
        id = kwargs.get('id', squish_string(title))
        size = kwargs.get('size', 'large')
        type = kwargs.get('type', 'hardhat').lower()
        h = kwargs.get('h')
        
        if type in ('fedora', 'hardhat', 'tophat'):
            if size.endswith('%'):
                percentage = float(size.strip('%')) / 100.0
                width, height = SIZES[type]['l']
            else:
                percentage = 1
                width, height = SIZES[type][size[0]]
            
            width = int(width * percentage)
            height = int(height * percentage)
        
        if h:
            if h == '1':
                root = tag.h1
            elif h == '2':
                root = tag.h2
            elif h == '3':
                root = tag.h3
            elif h == '4':
                root = tag.h4
            else:
                root = tag.h5
        else:
            s0 = size[0]
            if s0 == 'l':
                root = tag.h1
            elif s0 == 'm':
                root = tag.h2
            elif s0 == 's':
                root = tag.h3
            else:
                root = tag.h1
        
        url = get_absolute_url(formatter.href.base, 'htdocs://sixhats/img/%(type)s/%(hat)s.jpg' % {'type': type, 'hat': hat})
        
        if id:
            return root(id=id)(tag.img(src=url, width=width, height=height), title)
        else:
            return root()(tag.img(src=url, width=width, height=height), title)
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """ Makes the 'htdocs' folder inside the egg available.
        """
        from pkg_resources import resource_filename
        return [('sixhats', resource_filename('sixhats', 'htdocs'))]
    
    def get_templates_dirs(self):
        return []  # must return an iterable
