import os
import            logging
from copy  import deepcopy

logger = logging.getLogger(__name__)

NOT_RUN = 0
RUN     = 1
FAILED  = 2
    
class ProcessorSetup(object):
  def __init__(self, library, processor_classes, processor_settings, restrict_to = None):
    self.library            = library
    self.processor_classes  = list(processor_classes)
    self.processor_settings = processor_settings
    self.restrict_to        = restrict_to
    self._init_run          = False
    
  def _fetch_dependencies(self, processor_class, processor_map):
    dep_map = {}
    deps    = []

    def _fill_deps(processor_deps):
      for dep_id in processor_deps:
        if dep_id in dep_map:
          raise Exception('%s has a circular dependency chain. Detection occured at: %s' % (processor_class.id(), dep_id))

        dep_class = processor_map.get(dep_id)
        
        if dep_class == None:
          raise Exception('%s depends on an unknown processor class called %s' % (processor_class.id(), dep_id))
        
        dep_map[dep_id] = True
        deps.append(dep_id)
        
        _fill_deps(dep_class.depends_on())
      
    _fill_deps(processor_class.depends_on())

    deps.reverse()

    return deps
        
  def _maybe_init(self):
    if self._init_run:
      return

    processor_map   = { }
    processor_chain = { }
    processor_deps  = { }

    for p_class in self.processor_classes:
      try:
        settings = self.processor_settings.get(p_class.id(), {})
      
        processor_map[ p_class.id() ] = p_class(self.library, settings)
      except:
        logger.exception('[processor:%s] Unable to initialize' % p_class.id())
        
        raise
        
    for p_class in self.processor_classes:
      processor_deps[ p_class.id() ]  = self._fetch_dependencies(p_class, processor_map)
      processor_chain[ p_class.id() ] = list(processor_deps[ p_class.id() ])
      
      processor_chain[ p_class.id() ].append(p_class.id())

    self.processor_map   = processor_map
    self.processor_chain = processor_chain
    self.processor_deps  = processor_deps

  def runner(self):
    self._maybe_init()
    
    processor_ids = [p.id() for p in self.restrict_to or self.processor_classes]
    
    return ProcessorRunner(processor_ids, self.processor_map, self.processor_chain, self.processor_deps)
    
class ProcessorRunner(object):
  def __init__(self, processor_ids, processor_map, processor_chain, processor_deps):
    self.processor_ids   = processor_ids
    self.processor_map   = processor_map
    self.processor_chain = processor_chain
    self.processor_deps  = processor_deps
    self.full_run        = len(processor_ids) == len(processor_map.keys())
    self.run_state       = {}
    self.save_states     = {}
    self.clean_states    = {}
    
  def _init_for_object(self, o):
    self.run_state    = {}
    self.save_states  = {}
    self.clean_states = {}
    
  def get_run_state(self, o, processor_id):
    return self.run_state.get(processor_id, NOT_RUN)

  def set_run_state(self, o, processor_id, state):
    self.run_state[processor_id] = state
    
  def log_prefix(self, o):
    return '%s:%s' % (o.__class__.__name__, o.id)

  def process(self, o):
    self._init_for_object(o)

    prefix  = self.log_prefix(o)

    logger.debug('[%s] Starting processors' % prefix)

    success = True

    for processor_id in self.processor_ids:
      if not self.run_processor_chain(processor_id, o):
        success = False

    for processor, state in self.save_states.values():
        self.set_state(o, processor, state)
    
    for processor, state in self.clean_states.values():
      try:
        processor.cleanup(o, state)
      except:
        logger.exception('[%s] Unable to clean state for processor:%s' % (prefix, processor.id()))
        
    if success and self.full_run:
      o.processing_done = True

    try:
      o.save()
    except:
      logger.exception('[%s] Unable to save' % prefix)

  def run_processor_chain(self, processor_id, o):
    success = True
    prefix  = self.log_prefix(o)
    
    logger.debug('[%s] Starting processor run for: %s - chain: %s' % (prefix, processor_id, self.processor_chain[processor_id]))

    for run_id in self.processor_chain[processor_id]:
      state = self.get_run_state(o, run_id)

      if state == RUN:
        logger.debug("[%s] Dependent processor: %s has already been run, skipping" % (prefix, run_id))

        continue
      elif state == FAILED:
        logger.error("[%s] Unable to run process: %s - dependent processor: %s failed to run" % (prefix, processor_id, run_id))

        break
      elif state == NOT_RUN:
        logger.debug('[%s] Running processor:%s' % (prefix, run_id))

        try:          
          self.run_processor(o, run_id)

          self.set_run_state(o, run_id, RUN)
        except:
          self.set_run_state(o, run_id, FAILED)

          success = False

          logger.exception('[%s] Unable to run processor:%s' % (prefix, run_id))

          break
      else:
        raise Exception('Unsupported run state: %s while running processor: %s' % (state, processor_id))
        
    return success
        
  def run_processor(self, o, processor_id):
    processor = self.processor_map[processor_id]

    old_state  = self.state(o, processor)
    dep_states = self.dependent_states(o, self.processor_deps[processor_id])

    new_state = processor.process(o, old_state, dep_states)

    # We only want to record/clean up states if they have changed
    if new_state != old_state:
      self.clean_states[processor_id] = (processor, old_state)
      self.save_states[processor_id]  = (processor, new_state)

  def cleanup(self, o):
    prefix  = self.log_prefix(o)

    logger.debug('[%s] Running cleanup for processors' % prefix)

    try:
      for processor_id in self.processor_ids:
        processor = self.processor_map[processor_id]

        old_state = self.state(o, processor)
        
        logger.debug('[%s] Running cleanup for processor:%s' % (prefix, processor.id()))
      
        try:
          processor.cleanup(o, old_state)
        except:
          logger.exception('[%s] Unable to cleanup processor:%s' % (prefix, processor.id()))
          
        self.remove_state(o, processor)
        
      o.save()
    except:
      logger.exception('[%s] Processing cleanup failed' % prefix)

  def state(self, o, processor):
    return o.processor_state.get(processor.id(), processor.default_state())
    
  def remove_state(self, o, processor):
    o.processor_state.pop(processor.id(), None)
    
  def set_state(self, o, processor, state):
    o.processor_state[ processor.id()] = state
    
  def dependent_states(self, o, dependency_ids):
    states = {}
    
    for dependency_id in dependency_ids:
      if dependency_id in self.save_states:
        states[ dependency_id ] = self.save_states[dependency_id][1]
      else:
        states[ dependency_id ] = self.state(o, self.processor_map[dependency_id])
      
    return states