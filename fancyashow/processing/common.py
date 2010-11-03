import logging
from datetime import datetime

RESOURCE_HANDLED         = 0
RESOURCE_HANDLING_FAILED = 1
RESOURCE_NOT_HANDLED     = 2

class ResourceHandlerProcessorMixin(object):
  def resources(self, obj, state, dependent_states):
    raise NotImplementedError()
    
  def handlers(self):
    raise NotImplementedError()
    
  def log_prefix(self, o):
    return '%s:%s' % (o.__class__.__name__, o.id)

  def process(self, o, state, dependent_states):
    new_state = self.clone_state(state)
    prefix    = self.log_prefix(o)

    handlers = self.handlers()
    
    logging.debug("processing")

    for resource in self.resources(o, state, dependent_states):
      resource_state = new_state.get(resource, { })

      for handler in handlers:
        handler_id = handler.id()

        if handler.supports(resource):
          logging.debug('[%s] %s - Resource handler: %s supports resource' % (prefix, resource, handler_id))

          if handler_id in resource_state:
            logging.debug('[%s] %s - Resource handler: %s has already been run' % (prefix, resource, handler_id))
          else:
            logging.debug('[%s] %s - Resource handler: %s needs to be run ' % (prefix, resource, handler_id))
            
            handler_state = {
              'date': datetime.now()
            }

            try:
              handled = handler.handle(o, resource)
              
              if handled:
                handler_state['state'] = RESOURCE_HANDLED
              else:
                handler_state['state'] = RESOURCE_NOT_HANDLED
            except Exception, e:
              logging.exception('[%s] %s - Resource handler: %s failed to run' % (prefix, resource, handler_id))

              handler_state['state'] = RESOURCE_HANDLING_FAILED
              handler_state['error'] = str(e) 
              
            resource_state[handler_id] = handler_state

      if resource_state:
        new_state[resource] = resource_state
      
    return new_state

  def cleanup(self, o, state):
    return { }