## Ode Physics Addon for Blender
## by Hart, Dec 6th 2011
## License: BSD

import os, sys, time, ctypes
import bpy, mathutils
from bpy.props import *
from random import *
## make sure we can import from same directory ##
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path: sys.path.append( SCRIPT_DIR )
import ode

def _None(arg): return None		# stupid rule, why should the func have to return None - TODO talk to ideasman again.


#################### pyRNA ##################
bpy.types.Object.ode_use_body = BoolProperty( 
	name='use physics body', default=False, 
	update=lambda self,con:  ENGINE.get_wrapper(self).toggle_body(self.ode_use_body)
)


bpy.types.Object.ode_use_gravity = BoolProperty( 
	name='use gravity', default=True,		# ode defaults to True
	update=lambda self, con: ENGINE.get_wrapper(self).body.SetGravityMode(self.ode_use_gravity)
)

bpy.types.Object.ode_mass = FloatProperty( 
	name='body mass', default=1.0,
	update=lambda self, con: ENGINE.get_wrapper(self).set_mass(self.ode_mass)
)

bpy.types.Object.ode_linear_damping = FloatProperty( 
	name='linear damping', default=0.0420,
	update=lambda self, con: _None( ENGINE.get_wrapper(self).body.SetLinearDamping( self.ode_linear_damping ) )
)

bpy.types.Object.ode_angular_damping = FloatProperty( 
	name='angular damping', default=0.1,
	update=lambda self, con: _None( ENGINE.get_wrapper(self).body.SetAngularDamping( self.ode_angular_damping ) )
)


bpy.types.Object.ode_use_collision = BoolProperty( 
	name='use collision', default=False,
	update=lambda self, con: ENGINE.get_wrapper(self).toggle_collision(self.ode_use_collision)
)



########################## updated by devices ####################
bpy.types.Object.ode_constant_global_force = FloatVectorProperty( name='constant global force' )	
bpy.types.Object.ode_constant_local_force = FloatVectorProperty( name='constant local force' )
bpy.types.Object.ode_constant_global_torque = FloatVectorProperty( name='constant global torque' )
bpy.types.Object.ode_constant_local_torque = FloatVectorProperty( name='constant local torque' )

########################## updated by devices ####################
bpy.types.Object.ode_global_force = FloatVectorProperty( name='global force' )	
bpy.types.Object.ode_local_force = FloatVectorProperty( name='local force' )
bpy.types.Object.ode_global_torque = FloatVectorProperty( name='local torque' )
bpy.types.Object.ode_local_torque = FloatVectorProperty( name='local torque' )
#################################################################
bpy.types.Object.ode_force_driver_rate = FloatProperty( name='force driver rate', default=0.420, min=.0, max=1.0 )


def _set_gravity(world,context):
	x,y,z = world.ode_gravity
	ENGINE.world.SetGravity( x,y,z )
bpy.types.World.ode_gravity = FloatVectorProperty( 'gravity', min=-20, max=20, default=(.0,.0,-9.810), update=_set_gravity )

bpy.types.World.ode_ERP = FloatProperty(
	'error reduction param', min=.0, max=1.0, default=0.2,
	update= lambda w,c: _None( ENGINE.world.SetERP(w.ode_ERP) )
)
bpy.types.World.ode_CFM = FloatProperty(
	'constant force mixing', min=.00001, max=10.0, default=.00001,
	update= lambda w,c: _None( ENGINE.world.SetCFM(w.ode_CFM) )
)
bpy.types.World.ode_quickstep_iterations = IntProperty( 'quick step iterations', min=1, max=64, default=20 )

bpy.types.World.ode_linear_damping = FloatProperty(
	'linear damping', min=.0, max=10.0, default=.0,
	update= lambda w,c: _None( ENGINE.world.SetLinearDamping(w.ode_linear_damping) )
)
bpy.types.World.ode_angular_damping = FloatProperty(
	'angular damping', min=.0, max=10.0, default=.0,
	update= lambda w,c: _None( ENGINE.world.SetAngularDamping(w.ode_angular_damping) )
)





class ActivePhysicsWorldPanel(bpy.types.Panel):
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "physics"
	bl_label = "ODE Physics - World"
	@classmethod
	def poll(cls, context): return True

	def draw(self, context):
		layout = self.layout

		box = layout.box()
		box.label(text="Scene:")
		row = box.row()

		if ActivePhysics.active:
			row.operator(DisableOp.bl_idname, text="Disable")
		else:
			row.operator(EnableOp.bl_idname, text="Enable")


		if bpy.data.texts:
			row.operator(ReloadUserCallbackOp.bl_idname, text="Reload User Callback")
		else:
			row.label(text='user callback requires a text')

		row = box.row()
		row.prop( context.scene, 'use_gravity', text='Gravity' )
		row.prop( context.scene, 'gravity', text='' )
		row = box.row()
		row.prop( context.scene.game_settings, 'fps' )
		row.prop( context.scene.game_settings, 'physics_gravity', text='springy' )

# setFDir1
#def setFDir1(self, fdir):
#"""setFDir1(fdir)
#
#Set the "first friction direction" vector that defines a direction
#along which frictional force is applied. It must be of unit length
#and perpendicular to the contact normal (so it is typically
#tangential to the contact surface).
#
#@param fdir: Friction direction
#@type fdir: 3-sequence of floats
#"""
#self._contact.fdir1[0] = fdir[0]
#self._contact.fdir1[1] = fdir[1]
#self._contact.fdir1[2] = fdir[2]

#[flags specifies how contacts should be generated if the objects
#touch. Currently the lower 16 bits of flags specifies the maximum
#number of contact points to generate. If this number is zero, this
#function just pretends that it is one - in other words you can not
#ask for zero contacts. All other bits in flags must be zero. In
#the future the other bits may be used to select other contact
#generation strategies.]


class OdeSingleton(object):
	def reset( self ): [ ob.reset() for ob in self.objects.values() ]
	def start(self): self.active=True; self.reset(); print('starting ODE physics...')
	def stop(self): self.active=False; self.reset(); print('stopping ODE physics.')
	def exit(self): ode.CloseODE()
	def toggle_pause(self,switch):
		self.paused = switch

	def __init__(self):
		self.active = False
		self.paused = False
		ode.InitODE()
		self.world = ode.WorldCreate()
		self.world.SetGravity(.0,.0,-9.810)
		#self.world.SetQuickStepNumIterations(24)
		print( 'creating space' )
		self.space = ode.SimpleSpaceCreate()
		#self.space = ode.QuadTreeSpaceCreate(None, center4, extents4, depth)
		print( self.space )
		self.joint_group = ode.JointGroupCreate( 0 )		# max size (returns low-level pointer)
		self.objects = {}
		self.bodies = {}
		self._tmp_joints = []

	def get_wrapper(self, ob):
		if ob.name not in self.objects: self.objects[ ob.name ] = Object( ob, self.world, self.space )
		return self.objects[ ob.name ]

	def sync( self, context, recording=False ):
		if not self.active: return

		if context.active_object and context.active_object.name in self.objects:
			obj = self.objects[ context.active_object.name ]
			body = obj.body
			if body:
				x1,y1,z1 = body.GetPosition()
				#x2,y2,z2 = context.active_object.location
				x2,y2,z2 = context.active_object.matrix_world.to_translation()
				dx = x1-x2
				dy = y1-y2
				dz = z1-z2

				fudge = 0.5
				if context.blender_has_cursor or abs( x1-x2 ) > fudge or abs( y1-y2 ) > fudge or abs( z1-z2 ) > fudge:
					body.SetPosition( x2, y2, z2 )
					if not self.paused: body.AddForce( dx, dy, dz )

		if self.paused: return

		fast = []	# avoids dict lookups below
		for ob in bpy.data.objects:
			if ob.name not in self.objects: self.objects[ ob.name ] = Object( ob, self.world, self.space )
			obj = self.objects[ ob.name ]
			obj.sync( ob )		# gets new settings, calls AddForce etc...
			fast.append( (obj,ob) )

		fps = context.scene.game_settings.fps
		rate = 1.0 / fps


		ode.SpaceCollide( self.space, None, self.near_callback )
		#print( '------------- space collide complete -------------' )
		self.world.QuickStep( rate )
		#print( '------------- quick step complete -------------' )
		ode.JointGroupEmpty( self.joint_group )
		#print( '------------- joint group empty complete -------------', self._tmp_joints )

		if fast:
			for obj, bo in fast: obj.update( bo, recording )		# updates blender object for display



	PYOBJP = ctypes.POINTER(ctypes.py_object)
	def near_callback( self, data, geom1, geom2 ):
		#print( 'near callback', geom1, geom2 )	# geom1,2 are lowlevel pointers, not wrapper objects
		body1 = ode.GeomGetBody( geom1 )
		body2 = ode.GeomGetBody( geom2 )
		_b1 = _b2 = None
		try: _b1 = body1.POINTER.contents
		except ValueError: pass
		try: _b2 = body2.POINTER.contents
		except ValueError: pass
		if not _b1 and not _b2: return

		ptr1 = ctypes.cast( ode.GeomGetData( geom1 ), self.PYOBJP )
		ob1 = ptr1.contents.value
		ptr2 = ctypes.cast( ode.GeomGetData( geom2 ), self.PYOBJP )
		ob2 = ptr2.contents.value

		dContactGeom = ode.ContactGeom.CSTRUCT		# get the raw ctypes struct

		geoms = (dContactGeom * 32)()
		geoms_ptr = ctypes.pointer( geoms )
		touching = ode.Collide( 
			geom1, 
			geom2,
			32,	# flags, actually number of 
			geoms_ptr,
			ctypes.sizeof( dContactGeom )
		)

		dContact = ode.Contact.CSTRUCT			# get the raw ctypes struct
		for i in range(touching):
			g = geoms_ptr.contents[ i ]
			con = dContact()
			con.surface.mode = ode.ContactBounce	# pyode default
			#con.surface.bounce = 0.1				# pyode default
			con.surface.mu = 100.0
			con.geom = g

			## user callbacks ##
			dojoint = True
			cmd = ob1.callback( ob2, con, g.pos, g.normal, g.depth, i, touching )
			if cmd == 'BREAK': break
			elif cmd == 'PASS': dojoint = False
			cmd = ob2.callback( ob1, con, g.pos, g.normal, g.depth, i, touching )
			if cmd == 'BREAK': break
			elif cmd == 'PASS': dojoint = False

			if dojoint:
				joint = ode.JointCreateContact( self.world, self.joint_group, ctypes.pointer(con) )
				joint.Attach( body1, body2 )
				#print('friction', con.surface.mu)


ENGINE = OdeSingleton()
ActivePhysics = ENGINE





############################# object ##########################





class ActivePhysicsMaterialPanel(bpy.types.Panel):
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "physics"
	bl_label = "ODE Physics - Material"
	@classmethod
	def poll(cls, context):
		if context.active_object and context.active_object.type == 'MESH':
			if context.active_object.data.materials:
				if not context.active_object.game.use_ghost: return True

	def draw(self, context):
		layout = self.layout
		mat = context.active_object.data.materials[0]
		box = layout.box()
		box.label(text="Material: %s" %mat.name)
		box.prop( mat.physics, 'friction', text='Friction' )
		box.prop( mat.physics, 'fh_force', text='Bounce' )
		box.prop( mat.physics, 'fh_distance', text='Bounce Velocity Threshold' )
		box.prop( mat.physics, 'fh_damping', text='Soft Error Reduction' )
		box.prop( mat.physics, 'elasticity', text='Soft Mixing Force' )



############################################################
class Joint( object ):
	Types = {
		'ball' : 'Ball',
		'hinge' : 'Hinge', 
		'slider' : 'Slider', 
		'universal' : 'Universal', 
		'dual-hinge' : 'Hinge2', 
		'fixed' : 'Fixed', 
		'angular-motor' : 'AMotor', 
		'linear-motor' : 'LMotor', 
		'planar' : 'Plane2D', 
		'slider-hinge' : 'PR',
		'slider-universal' : 'PU',
		'piston' : 'Piston',
	}
	Tooltips = {
		'ball' : 'simple ball and socket joint',
		'hinge' : 'simple hinge joint (rotoide)', 
		'slider' : 'simple slider joint (prismatic)', 
		'universal' : 'A universal joint is like a ball and socket joint that constrains an extra degree of rotational freedom. Given axis 1 on body 1, and axis 2 on body 2 that is perpendicular to axis 1, it keeps them perpendicular.', 
		'dual-hinge' : 'The hinge-2 joint is the same as two hinges connected in series, with different hinge axes. An example, shown in the above picture is the steering wheel of a car, where one axis allows the wheel to be steered and the other axis allows the wheel to rotate.', 
		'fixed' : 'simple fixed joint, can produce spring-like effects when used with high CFM', 
		'angular-motor' : 'An angular motor (AMotor) allows the relative angular velocities of two bodies to be controlled. The angular velocity can be controlled on up to three axes, allowing torque motors and stops to be set for rotation about those axes', 
		'linear-motor' : 'A linear motor (LMotor) allows the relative linear velocities of two bodies to be controlled. The linear velocity can be controlled on up to three axes, allowing torque motors and stops to be set for translation along those axes', 
		'planar' : 'The plane-2d joint acts on a body and constrains it to the Z == 0 plane.', 
		'slider-hinge' : 'A prismatic and rotoide joint (JointPR) combines a Slider (prismatic) and a Hinge (rotoide).',
		'slider-universal' : 'A prismatic-Universal joint (JointPU) combines a Slider (prismatic) between body1 and the anchor and a Universal joint at the anchor position. This joint provide 1 degree of freedom in translation and 2 degrees of freedom in rotation.',
		'piston' : 'A piston joint is similar to a Slider joint except that rotation around the translation axis is possible.',

	}
	
	Params = 'ERP CFM LoStop HiStop Vel FMax FudgeFactor Bounce StopERP StopCFM SuspensionERP SuspensionCFM'.split()

	def __init__(self, parent, child, name, type):
		self.parent = parent
		self.child = child
		self.name = name
		self.type = type
		self.joint = None
		self.breaking_threshold = None
		self.damage_threshold = None
		self.broken = False
		self.slaves = []		# sub-joints
		self.settings = ['type', 'breaking_threshold']	# for loading/saving TODO - or just save all simple py types?
		self.feedback = ode.JointFeedback()
		self.set_type( type )	# must be last

	def get_stress(self):
		s = []
		for vec in (self.feedback.f1, self.feedback.f2, self.feedback.t1, self.feedback.t2):
			x,y,z,null = vec
			s += [abs(x), abs(y), abs(z)]
		return sum(s) / float(len(s))

	def break_joint(self):	# do not actually delete the joint
		print('breaking joint',self.name)
		if self.broken: print('WARN: joint already broken')
		else:
			self.broken = True
			ode.JointDisable( self.joint )
			for joint in self.slaves:
				joint.break_joint()

	def restore(self):
		if self.broken:
			self.broken = False
			ode.JointEnable( self.joint )
			for joint in self.slaves:
				joint.restore()

	def damage(self,value):
		#erp = self.get_param( 'ERP' )
		#self.set_param('ERP', 0.1)
		#self.set_param('CFM', 0.1)
		#self.child.increase_mass( value )
		#self.parent.increase_mass( value*0.25 )
		bpy.data.objects[ self.child.name ].ode_constant_global_force[2] -= value * 10
		bpy.data.objects[ self.parent.name ].ode_constant_global_force[2] -= value * 20
		#self.breaking_threshold *= 0.9
		#print('breaking thresh reduced to', self.breaking_threshold)

	def repair(self,value): pass


	def __del__(self):
		print('deleting joint',self.name)
		ode.JointDestroy( self.joint )

	def is_active(self): return bool( ode.JointIsEnabled(self.joint) )

	def toggle(self,switch):
		if switch: ode.JointEnable( self.joint )
		else: ode.JointDisable( self.joint )

	def set_type( self, type ):
		self.type = type					# nice name
		self.dtype = Joint.Types[type]		# ode name
		self._set_func = getattr( ode, 'JointSet%sParam'%self.dtype )
		self._get_func = getattr( ode, 'JointGet%sParam'%self.dtype )

		if self.joint: ode.JointDestroy(self.joint)
		world = self.parent.world
		func = getattr(ode, 'JointCreate%s'%self.dtype)
		self.joint = j = func( world )
		ode.JointAttach( j, self.parent.body, self.child.body )

		x,y,z = self.parent.body.GetPosition()

		if type == 'fixed': ode.JointSetFixed( j )
		elif type == 'angular-motor': pass
		elif type == 'linear-motor': pass
		elif type == 'planar': pass
		elif type == 'slider': pass

		elif type == 'ball': ode.JointSetBallAnchor(self.joint, x,y,z )
		elif type == 'hinge': ode.JointSetHingeAnchor(self.joint, x,y,z )
		elif type == 'universal':
			print('setting universal joint anchor', x,y,z)
			ode.JointSetUniversalAnchor(self.joint, x,y,z )
		elif type == 'dual-hinge':
			print('setting hinge2 joint anchor', x,y,z)
			ode.JointSetHinge2Anchor(self.joint, x,y,z )
		elif type == 'PR': ode.JointSetPRAnchor(self.joint, x,y,z )
		elif type == 'PU': ode.JointSetPUAnchor(self.joint, x,y,z )
		elif type == 'piston': ode.JointSetPistonAnchor(self.joint, x,y,z )
		else:
			print('ERROR: unknown joint type', type)
			assert 0

		ode.JointSetFeedback( self.joint, self.feedback )

	def set_param( self, param, *args ):
		assert param in Joint.Params
		print('setting joint param', param, args)
		if param not in self.settings: self.settings.append( param )

		P = getattr(ode, 'Param%s'%param)
		params = []
		for i in range(3): params.append( getattr(ode, 'Param%s%s' %(param,i+1)) )

		self._set_func( self.joint, P, args[0] )

		if len(args)==3:
			setattr(self,param,args)
			for i,p in enumerate(params):
				self._set_func( self.joint, p, args[i] )

		elif len(args)==1:
			setattr(self,param,args[0])
			for i,p in enumerate(params):
				self._set_func( self.joint, p, args[0] )

	def get_param(self, param):
		assert param in Joint.Params
		return self._get_func( self.joint, ode.ParamERP )

JOINT_TYPES = list(Joint.Types.keys())


####################### object wrapper ######################
class Object( object ):
	def pop_joint( self, name ): return self.joints.pop(name)
	def change_joint_type( self, name, type ): self.joints[name].set_type(type)
	def new_joint(self, other, name='default', type='fixed'):
		self.joints[name] = j = Joint(other,self,name,type)
		return j

	def set_mass( self, value ):
		print( 'set-mass',value )
		self.mass = mass = ode.Mass()
		mass.SetSphereTotal( value, 0.1)		# total mass, radius
		if self.body: self.body.SetMass( mass )

	def increase_mass( self, value ):
		assert self.mass
		m = ode.Mass()
		m.SetSphereTotal( value, 0.1)
		self.mass.Add( m )

	'''
	self.fx
		use actuator edit-object > track-to, but hijack reverse, target lamp or camera
		hijack linear vel, angular vel to use as thresholds for collision...
		... no good way to pick input event, device API?
		ok for now, collision always triggers if above thresh.

	'''
	def callback( self, other, contact, pos, normal, depth, hit_index, num_hits ):
		contact.surface.mu += self.get_friction( pos, normal, depth )
		contact.surface.bounce += self.get_bounce( pos, normal, depth )
		contact.surface.bounce_vel += self.get_min_bounce_vel( pos, normal, depth )
		contact.surface.soft_erp += self.get_collision_erp( pos, normal, depth )
		contact.surface.soft_cfm += self.get_collision_cfm( pos, normal, depth )
		#con.surface.motion1 = 0.1	# Set the surface velocity in friction direction 1.
		#con.surface.slip1 = 0.1		# Set the coefficient of force-dependent-slip (FDS) for friction direction 1.
		#return 'PASS'		# this passes this contact and goes onto the next, more contact joints maybe created.
		#print( self.get_linear_vel() )
		if hit_index > 16: return 'BREAK'	# prevents too many collision joints, speeds things up, max hits is 32

	def get_material(self):
		if self.type == 'MESH':
			bo = bpy.data.objects[ self.name ]
			if bo.data.materials:
				# only consider first material, since face/material lookup to pos is slow
				return bo.data.materials[0]

	def get_linear_vel( self ):
		if self.body: return self.body.GetLinearVel()		# localspace

	def get_average_linear_vel( self ):
		if self.body: 
			x,y,z = self.body.GetLinearVel()
			v = abs(x)+abs(y)+abs(z)
			return v/3.0

	def get_angular_vel( self ):
		if self.body: return self.body.GetAngularVel()



	###################################################
	def get_friction(self, pos, normal, depth ):
		mu = 0.0
		bo = bpy.data.objects[ self.name ]
		m = self.get_material()
		if m: mu += m.physics.friction
		return mu

	def get_bounce(self, pos, normal, depth ):
		bounce = 0.0
		bo = bpy.data.objects[ self.name ]
		if self.type == 'MESH':
			if bo.data.materials:
				# only consider first material, since face/material lookup to pos is slow
				m = bo.data.materials[0]
				bounce += m.physics.fh_force
		return bounce
	def get_min_bounce_vel(self, pos, normal, depth ):
		vel = 0.0
		bo = bpy.data.objects[ self.name ]
		if self.type == 'MESH':
			if bo.data.materials:
				# only consider first material, since face/material lookup to pos is slow
				m = bo.data.materials[0]
				vel += m.physics.fh_distance
		return vel
	def get_collision_erp(self, pos, normal, depth ):
		erp = 0.0
		bo = bpy.data.objects[ self.name ]
		if self.type == 'MESH':
			if bo.data.materials:
				# only consider first material, since face/material lookup to pos is slow
				m = bo.data.materials[0]
				erp += m.physics.fh_damping
		return erp
	def get_collision_cfm(self, pos, normal, depth ):
		cfm = 0.0
		bo = bpy.data.objects[ self.name ]
		if self.type == 'MESH':
			if bo.data.materials:
				# only consider first material, since face/material lookup to pos is slow
				m = bo.data.materials[0]
				cfm += m.physics.elasticity
		return cfm

	def toggle_collision(self, switch):
		if not switch and self.geom:
			self.geom.Destroy()
			self.geom = None
			print('destroyed geom')
		elif switch:
			ob = bpy.data.objects[ self.name ]
			pos,rot,scl = ob.matrix_world.decompose()
			px,py,pz = pos
			rw,rx,ry,rz = rot
			sx,sy,sz = scl
			if ob.type == 'MESH': sx,sy,sz = ob.dimensions

			T = ob.game.collision_bounds_type
			if T in 'BOX SPHERE CAPSULE CYLINDER'.split():		#TODO: CONVEX_HULL, TRIANGLE_MESH
				sradius = ((sx+sy+sz) / 3.0) *0.5
				cradius = ((sx+sy)/2.0) * 0.5
				length = sz
				self.geomtype = T
				if T == 'BOX': self.geom = ode.CreateBox( self.space, sx, sy, sz )
				elif T == 'SPHERE': self.geom = ode.CreateSphere( self.space, sradius )
				elif T == 'CAPSULE': self.geom = ode.CreateCapsule( self.space, cradius, length )
				elif T == 'CYLINDER': self.geom = ode.CreateCylinder( self.space, cradius, length )
				#elif T == 'CONVEX_HULL': self.geom = ode.CreateConvex( self.space, planes, numplanes, points, numpoints, polys )
				geom = self.geom
				geom.SetPosition( px, py, pz )
				geom.SetQuaternion( (rw,rx,ry,rz) )
				if self.body: geom.SetBody( self.body )

				print( 'created new geom', T, self.name )
				## this is safe ##
				self._geom_set_data_pointer = ctypes.pointer( ctypes.py_object(self) )
				geom.SetData( self._geom_set_data_pointer )

	def toggle_body(self, switch):
		if switch:
			if not self.body:
				print( 'created new body', self.name )

				ob = bpy.data.objects[self.name]
				pos,rot,scl = ob.matrix_world.decompose()
				px,py,pz = pos
				rw,rx,ry,rz = rot
				sx,sy,sz = scl
				if ob.type == 'MESH': sx,sy,sz = ob.dimensions

				print('SETTING NEW BODY POS', px,py,pz)

				self.body = body = ode.BodyCreate( self.world )
				ENGINE.bodies[ self.name ] = body
				body.SetPosition( px,py,pz )
				body.SetQuaternion( (rw,rx,ry,rz) )
				if self.geom: self.geom.SetBody( body )
				body.SetGravityMode( ob.ode_use_gravity )
				self.set_mass( ob.ode_mass )		# reset mass
				#if self.type=='EMPTY':
				#	ob.ode_use_gravity = False	# force empties not to use gravity


		elif self.body:
			ENGINE.bodies.pop( self.name )
			self.body.Destroy()
			self.body = None
			self.clear_body_config()
			print( 'body destroyed' )



	def __init__( self, bo, world, space ):	# do not hold reference to ob?
		self.world = world
		self.space = space
		self.name = bo.name
		self.type = bo.type
		self.config = cfg = {}
		self.recbuffer = []
		self.body = None
		self.geom = None
		self.geomtype = None
		self.joints = {}
		self.fx = {}	# cmd : arg
		self.alive = True
		self.save_transform( bo )

	def save_transform(self, bo):
		self.start_matrix = bo.matrix_world.copy()
		x,y,z = bo.matrix_world.to_translation()
		self.start_position = (x,y,z)
		w,x,y,z = bo.matrix_world.to_quaternion()
		self.start_rotation = (w,x,y,z)
		x,y,z = bo.matrix_world.to_scale()
		self.start_scale = (x,y,z)


	def reset(self):
		self.recbuffer = []
		name = self.name
		cfg = self.config
		ob = bpy.data.objects[ name ]
		body = self.body
		if body:
			ob.matrix_world = self.start_matrix.copy()
			x,y,z = self.start_position
			#loc = ob.location
			#loc.x = x; loc.y = y; loc.z = z	# restore transform
			body.SetPosition( x,y,z )
			w,x,y,z = self.start_rotation
			#q = ob.rotation_quaternion
			#q.w = w; q.x = x; q.y = y; q.z = z
			body.SetQuaternion( (w,x,y,z) )
			body.SetForce( .0, .0, .0 )
			body.SetTorque( .0, .0, .0 )
			body.SetLinearVel( .0, .0, .0 )
			body.SetAngularVel( .0, .0, .0 )


	def update( self, ob, recording=False ):
		if self.type == 'LAMP':
			if 'random-color' in self.fx:
				ob.data.color.r = random()
				ob.data.color.b = random()
				ob.data.color.g = random()
		if self.type in 'CAMERA LAMP'.split():
			if 'look-at' in self.fx:
				tt = None
				for con in cam.constraints:
					if con.type == 'TRACK_TO': tt = con; break
				if not tt: tt = ob.constraints.new( 'TRACK_TO' )
				tt.up_axis = 'UP_Y'
				tt.track_axis = 'TRACK_NEGATIVE_Z'
				if self.fx['look-at'] == MOST_KINEMATIC: pass
				else: tt.target = bpy.data.objects[ self.fx['look-at'] ]
		self.fx = {}

		body = self.body
		if not body or not self.alive: return

		#if geom:		# geoms don't move?
		#	px,py,pz = geom.GetPosition()
		#	rw,rx,ry,rz = geom.GetQuaternion()

		m = mathutils.Matrix()
		#x,y,z = ob.scale		# copy scale (local space?)
		#m[0][0] = x
		#m[1][1] = y
		#m[2][2] = z
		x,y,z = body.GetPosition()
		m[3][0] = x
		m[3][1] = y
		m[3][2] = z

		q = mathutils.Quaternion()
		qw,qx,qy,qz = body.GetQuaternion()
		q.w = qw; q.x=qx; q.y=qy; q.z=qz

		if recording:
			self.recbuffer.append( ((x,y,z),(qw,qx,qy,qz)) )

		x,y,z = ob.scale	# save scale
		ob.matrix_world = m * q.to_matrix().to_4x4()
		ob.scale = (x,y,z)	# restore scale

	def clear_body_config( self ):
		keys = list(self.config.keys())
		for key in keys:
			if key not in 'use_ghost collision_bounds_type'.split():
				self.config.pop( key )

	def sync( self, ob ):	# checks config
		cfg = self.config
		body = self.body
		geom = self.geom

		pos,rot,scl = ob.matrix_world.decompose()
		px,py,pz = pos
		rw,rx,ry,rz = rot
		sx,sy,sz = scl
		if ob.type == 'MESH': sx,sy,sz = ob.dimensions

		LIMIT = 10000
		if abs(px) > LIMIT or abs(py) > LIMIT or abs(pz) > LIMIT:
			if self.alive and body: body.Disable()
			self.alive = False
		if not self.alive: return


		if body:	# apply constant forces
			x,y,z = ob.ode_local_force
			if x or y or z: body.AddRelForce( x,y,z )
			x,y,z = ob.ode_global_force
			if x or y or z: body.AddForce( x,y,z )
			x,y,z = ob.ode_local_torque
			if x or y or z: body.AddRelTorque( x,y,z )
			x,y,z = ob.ode_global_torque
			if x or y or z: body.AddTorque( x,y,z )

			rate = ob.ode_force_driver_rate
			for vec in (ob.ode_local_force, ob.ode_global_force, ob.ode_local_torque, ob.ode_global_torque):
				vec[0] *= rate
				vec[1] *= rate
				vec[2] *= rate


			x,y,z = ob.ode_constant_local_force
			if x or y or z: body.AddRelForce( x,y,z )
			x,y,z = ob.ode_constant_global_force
			if x or y or z: body.AddForce( x,y,z )
			x,y,z = ob.ode_constant_local_torque
			if x or y or z: body.AddRelTorque( x,y,z )
			x,y,z = ob.ode_constant_global_torque
			if x or y or z: body.AddTorque( x,y,z )


		if geom and not body:
			## bodyless geoms should always get updates from blender
			geom.SetPosition( px, py, pz )
			geom.SetQuaternion( (rw,rx,ry,rz) )
			if self.geomtype in 'BOX SPHERE CAPSULE CYLINDER'.split():	# can do fast dynamic update of scaling
				sradius = ((sx+sy+sz) / 3.0) *0.5
				cradius = ((sx+sy)/2.0) * 0.5
				length = sz
				if self.geomtype == 'BOX': geom.BoxSetLengths( sx, sy, sz )
				elif self.geomtype == 'SPHERE': geom.SphereSetRadius( sradius )
				elif self.geomtype == 'CAPSULE': geom.CapsuleSetParams( sradius, length )
				elif self.geomtype == 'CYLINDER': geom.CylinderSetParams( sradius, length )



class ReloadUserCallbackOp(bpy.types.Operator):
	bl_idname = "active_physics.reload_user_callback"
	bl_label = "Reload User Collision Callback"
	bl_description = "collision callback"
	@classmethod
	def poll(cls, context): return True	#return context.mode!='EDIT_MESH'
	def invoke(self, context, event):
		txt = bpy.data.texts[0]
		exec( txt.as_string() )
		assert 'callback' in locals()
		setattr( Object, 'callback', locals()['callback'] )
		return {'FINISHED'}



class EnableOp(bpy.types.Operator):
	bl_idname = "active_physics.enable_ode"
	bl_label = "Toggle Active Physics"
	bl_description = "Toggle ..."
	@classmethod
	def poll(cls, context): return True	#return context.mode!='EDIT_MESH'
	def invoke(self, context, event):
		ActivePhysics.start()
		return {'FINISHED'}

class DisableOp(bpy.types.Operator):
	bl_idname = "active_physics.disable_ode"
	bl_label = "Disable Active Physics"
	bl_description = "end threads..."
	@classmethod
	def poll(cls, context): return True
	def invoke(self, context, event):
		ActivePhysics.stop()
		return {'FINISHED'}

class BodyEnableOp(bpy.types.Operator):
	bl_idname = "active_physics.body_enable"
	bl_label = "enable physics body"
	bl_description = "..."
	@classmethod
	def poll(cls, context): return True
	def invoke(self, context, event):
		game = context.active_object.game
		game.physics_type = 'DYNAMIC'
		return {'FINISHED'}
class BodyDisableOp(bpy.types.Operator):
	bl_idname = "active_physics.body_disable"
	bl_label = "disable physics body"
	bl_description = "..."
	@classmethod
	def poll(cls, context): return True
	def invoke(self, context, event):
		game = context.active_object.game
		game.physics_type = 'STATIC'		# in BGE static means non-moving, but may have collision
		return {'FINISHED'}


class GeomEnableOp(bpy.types.Operator):
	bl_idname = "active_physics.collision_enable"
	bl_label = "Enable Collision"
	bl_description = "..."
	@classmethod
	def poll(cls, context): return True
	def invoke(self, context, event):
		game = context.active_object.game
		game.use_ghost = False
		#context.active_object.game.physics_type = 'DYNAMIC'
		return {'FINISHED'}
class GeomDisableOp(bpy.types.Operator):
	bl_idname = "active_physics.collision_disable"
	bl_label = "Disable Collision"
	bl_description = "..."
	@classmethod
	def poll(cls, context): return True
	def invoke(self, context, event):
		game = context.active_object.game
		game.use_ghost = True
		#if game.physics_type == 'DYNAMIC': game.physics_type = 'STATIC'
		#else: game.physics_type = 'NO_COLLISION'
		return {'FINISHED'}




#########################################

bpy.utils.register_module(__name__)

