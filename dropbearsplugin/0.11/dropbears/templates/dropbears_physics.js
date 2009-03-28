Event.observe(window, 'load', function() {
  var worldAABB = new b2AABB();
  worldAABB.minVertex.Set(0, 0);
  worldAABB.maxVertex.Set(document.width, document.height);
  var gravity = new b2Vec2(0, 300);
  var doSleep = true;
  var world = new b2World(worldAABB, gravity, doSleep);
  var radius = 20;
  var cursor = new b2Vec2(0, 0);
  
  var cursorSd = new b2CircleDef();
  cursorSd.density = 1.0;
  cursorSd.radius = radius;
  cursorSd.restitution = 1.0;
  cursorSd.friction = 0;
  var cursorBd = new b2BodyDef();
  cursorBd.AddShape(cursorSd);
  cursorBd.position.Set(radius, radius);
  var cursor = world.CreateBody(cursorBd);

  function mouseX(evt) {
    if (evt.pageX) return evt.pageX;
    else if (evt.clientX)
      return evt.clientX + (document.documentElement.scrollLeft ?
        document.documentElement.scrollLeft :
        document.body.scrollLeft);
    else return null;
  }
  function mouseY(evt) {
    if (evt.pageY) return evt.pageY;
    else if (evt.clientY)
      return evt.clientY + (document.documentElement.scrollTop ?
        document.documentElement.scrollTop :
        document.body.scrollTop);
    else return null;
  }
    
  Event.observe(window, 'mousemove' function(evt) {
    cursor.m_position.x = mouseX(evt);
    cursor.m_position.y = mouseY(evt);
  });
  
  function make_bear()
  {
    var bear = jQuery('<img class="dropbear" src="${href.chrome('dropbear', 'dropbear.gif')}" alt="DROPBEAR!" />');
    bear.appendTo('body');
  
    var circleSd = new b2CircleDef();
    circleSd.density = 1.0;
    circleSd.radius = radius;
    circleSd.restitution = 1.0;
    circleSd.friction = 0;
    var circleBd = new b2BodyDef();
    circleBd.AddShape(circleSd);
    circleBd.position.Set(Math.round((document.width-radius) * Math.random())+radius, radius);
    circleBd.userData = bear;
    var circleBody = world.CreateBody(circleBd);
  }
  
  function step() {
    world.Step(1.0/60, 1);
    for (var b = world.m_bodyList; b; b = b.m_next) {
      if(b.m_position.y + radius > document.height)
      {
        b.m_position.y = radius;
        b.m_position.x = Math.round((document.width-radius) * Math.random())+radius;
        b.m_linearVelocity.x = 0;
        b.m_linearVelocity.y = 0;
      }
      
      if(b.m_userData)
      {
        var x = b.m_position.x - radius;
        var y = b.m_position.y - radius;
        b.m_userData.css('top', y+'px').css('left', x+'px');
      }
    }
    setTimeout(step, 10);
  }
  
#for i in xrange(dropbears)
  make_bear();
#end
  
  step();
});