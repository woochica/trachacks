# ===========================================================================
# Thanks to osimons for this excellent Python method replacement wizardry...
#
# ===========================================================================

def wrapfunc(obj, name, processor, avoid_doublewrap=True):
     """ patch obj.<name> so that calling it actually calls, instead,
             processor(original_callable, *args, **kwargs)

     Function wrapper (wrap function to extend functionality)
     Implemented from Recipe 20.6 / Python Cookbook 2. edition

     Example usage of funtion wrapper:

     def tracing_processor(original_callable, *args, **kwargs):
         r_name = getattr(original_callable, '__name__', '<unknown>')
         r_args = map(repr, args)
         r_args.extend(['%s=%s' % x for x in kwargs.iteritems()])
         print "begin call to %s(%s)" % (r_name, ", ".join(r_args))
         try:
             result = original_callable(*args, **kwargs)
         except:
             print "EXCEPTION in call to %s" % (r_name,)
             raise
         else:
             print "call to %s result: %r" % (r_name, result)
             return result

     def add_tracing_prints_to_method(class_object, method_name):
         wrapfunc(class_object, method_name, tracing_processor)
     """
     # get the callable at obj.<name>
     call = getattr(obj, name)
     # optionally avoid multiple identical wrappings
     if avoid_doublewrap and getattr(call, 'processor', None) is processor:
         return
     # get underlying function (if any), and anyway def the wrapper closure
     original_callable = getattr(call, 'im_func', call)
     def wrappedfunc(*args, **kwargs):
         return processor (original_callable, *args, **kwargs)
     # set attributes, for future unwrapping and to avoid double-wrapping
     wrappedfunc.original = call
     wrappedfunc.processor = processor
     # 2.4 only: wrappedfunc.__name__ = getattr(call, '__name__', name)
     # rewrap staticmethod and classmethod specifically (if obj is a class)
     import inspect
     if inspect.isclass(obj):
         if hasattr(call, 'im_self'):
             if call.im_self:
                 wrappedfunc = classmethod(wrappedfunc)
         else:
             wrappedfunc = staticmethod(wrappedfunc)
     # finally, install the wrapper closure as requested
     setattr(obj, name, wrappedfunc)


def unwrapfunc(obj, name):
     """ undo the effects of wrapfunc(obj, name, processor) """
     setattr(obj, name, getattr(obj, name).original)
