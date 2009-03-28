from trac.core import *
from trac.web.main import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.prefs.api import IPreferencePanelProvider
from trac.config import IntOption

class DropbearFilter(Component):
    """A filter to show dropbears."""
    
    default_dropbears = IntOption('dropbears', 'default', default=0,
                                  doc='The number of dropbears to show by default.')
    
    implements(IRequestFilter, IRequestHandler, ITemplateProvider, IPreferencePanelProvider)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if int(req.session.get('dropbears', self.default_dropbears)):
            add_stylesheet(req, 'dropbear/dropbears.css')
            if req.session.get('dropbears_physics'):
                add_script(req, 'dropbear/js/prototype-1.6.0.2.js')
                add_script(req, 'dropbear/js/box2d/common/b2Settings.js')
                add_script(req, 'dropbear/js/box2d/common/math/b2Vec2.js')
                add_script(req, 'dropbear/js/box2d/common/math/b2Mat22.js')
                add_script(req, 'dropbear/js/box2d/common/math/b2Math.js')
                add_script(req, 'dropbear/js/box2d/collision/b2AABB.js')
                add_script(req, 'dropbear/js/box2d/collision/b2Bound.js')
                add_script(req, 'dropbear/js/box2d/collision/b2BoundValues.js')
                add_script(req, 'dropbear/js/box2d/collision/b2Pair.js')
                add_script(req, 'dropbear/js/box2d/collision/b2PairCallback.js')
                add_script(req, 'dropbear/js/box2d/collision/b2BufferedPair.js')
                add_script(req, 'dropbear/js/box2d/collision/b2PairManager.js')
                add_script(req, 'dropbear/js/box2d/collision/b2BroadPhase.js')
                add_script(req, 'dropbear/js/box2d/collision/b2Collision.js')
                add_script(req, 'dropbear/js/box2d/collision/Features.js')
                add_script(req, 'dropbear/js/box2d/collision/b2ContactID.js')
                add_script(req, 'dropbear/js/box2d/collision/b2ContactPoint.js')
                add_script(req, 'dropbear/js/box2d/collision/b2Distance.js')
                add_script(req, 'dropbear/js/box2d/collision/b2Manifold.js')
                add_script(req, 'dropbear/js/box2d/collision/b2OBB.js')
                add_script(req, 'dropbear/js/box2d/collision/b2Proxy.js')
                add_script(req, 'dropbear/js/box2d/collision/ClipVertex.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2Shape.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2ShapeDef.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2BoxDef.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2CircleDef.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2CircleShape.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2MassData.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2PolyDef.js')
                add_script(req, 'dropbear/js/box2d/collision/shapes/b2PolyShape.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2Body.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2BodyDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2CollisionFilter.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2Island.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2TimeStep.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2ContactNode.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2Contact.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2ContactConstraint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2ContactConstraintPoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2ContactRegister.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2ContactSolver.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2CircleContact.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2Conservative.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2NullContact.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2PolyAndCircleContact.js')
                add_script(req, 'dropbear/js/box2d/dynamics/contacts/b2PolyContact.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2ContactManager.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2World.js')
                add_script(req, 'dropbear/js/box2d/dynamics/b2WorldListener.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2JointNode.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2Joint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2JointDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2DistanceJoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2DistanceJointDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2Jacobian.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2GearJoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2GearJointDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2MouseJoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2MouseJointDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2PrismaticJoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2PrismaticJointDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2PulleyJoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2PulleyJointDef.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2RevoluteJoint.js')
                add_script(req, 'dropbear/js/box2d/dynamics/joints/b2RevoluteJointDef.js')
                add_script(req, '/dropbear/dropbears.js?physics=1')
            else:
                add_script(req, '/dropbear/dropbears.js?physics=0')
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/dropbear')
        
    def process_request(self, req):
        data = {}
        data['dropbears'] = int(req.session.get('dropbears', self.default_dropbears))
        data['dropbears_physics'] = req.session.get('dropbears') or None
        template = data['dropbears_physics'] and 'dropbears_physics.js' or 'dropbears.js'
        return template, data, 'text/plain'
        
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('dropbear', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        yield 'dropbears', 'Dropbears'
        
    def render_preference_panel(self, req, panel):
        if req.method == 'POST':
            req.session['dropbears'] = req.args.get('dropbears', '')
            req.session['dropbears_physics'] = req.args.get('dropbears_physics', '')
            req.redirect(req.href.prefs(panel))
        
        data = {}
        data['dropbears'] = int(req.session.get('dropbears', self.default_dropbears))
        data['dropbears_physics'] = req.session.get('dropbears_physics') or None
        return 'prefs_dropbears.html', data