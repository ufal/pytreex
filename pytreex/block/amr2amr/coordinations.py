#Silvie's training function 01
#2015-06-19
#spust makefile pro vystup do penmana bez tsurgeona a
# prohlidni si, jak vypada struktura uzlu.         Udelano.

#Odusek has to explain how to look at t-nodes from an AMR tree
#teprve napise API, ale formulaci uz prozradil
from __future__ import unicode_literals

from alex.components.nlg.tectotpl.core.block import Block
from alex.components.nlg.tectotpl.core.exception import LoadingException
from alex.components.nlg.tectotpl.tool.lexicon.cs import Lexicon

__author__ = "Silvie Cinková"
__date__ = "2015"                                                                                                         
                    
class Coordinations(Block):
    """
    Build the AMR cooordination structure for two+ coordination
    members according to the AMR manual, Conjunctions). 
    Normally, a coordination has the conjunction on top and its members are 
    numbered like this:
    "boy and girl" 
   (a / and
      :op1 (b / boy)
      :op2 (g / girl)
      )
    "the boy shouted and left"
    (a / and                                                                                                                                          
    :op1 (c / shout-01)                                                                                                                              
    :op2 (l / leave-01                                                                                                                               
           :ARG0 (b / boy)))
  
    "the boy who shouted and left"
    (:b/boy
     ARG0-of(a / and
     :op1 (s / shout-01)
     :op2 (l / leave-01)
     )
    )
  
    On the other hand, coordinated non-clausal modifiers of a noun are
    captured like this: 
    "big and heavy ball"
     (b / ball
   :mod (b2 / big)
   :mod (h / heavy))
    """                                                                                      
    
    def __init__(self, scenario, args):                                               
        "Constructor, just checking the argument values"                              
        Block.__init__(self, scenario, args)                                          
        if self.language is None:                                                     
           raise LoadingException('Language must be defined!')                        
        self.lexicon = Lexicon()                                                      
                                                                                      
    def process_amrnode(self, amrnode): #never change this function name              
        """..."""                                                                            
      tnode = amrnode.src_tnode                                         
      if tnode is None: 
        return
      if tnode.nodetype != 'coap':
        return
      if tnode.functor == 'APPS':
        return
      tparent = tnode.parent     
      amrchildren =  amrnode.get_children()   
      tchildren = tnode.get_children()
                
      if CoordRules.is_noun_attribute(tnode, tparent=tparent): #tparent 
      #vlevo je nazev parametru, jen nahodou uz mam stejne 
      #pojmenovanou promennou, kterou jsem si predpocitala na zacatku 
          amrparent = amrnode.parent
          for amrchild in amrchildren:
              amrchild.parent = amrparent #@property def(parent), node.py 
              #l. 331, @parent setter, node.py l. 342 - tady vlastne nastavuju 
              #hodnotu atributu 
              amrchild.modifier = 'mod' #provides children with label
          amrnode.remove() #removes the coordination amr node 
      if not CoordRules.is_noun_attribute(tnode, tparent=tparent):
          opnum = 1
          for amrchild in amrchildren:
              if (tchild is None and some_coordmember_there == False ): 
              #pojmenovane entity, typ Franta Novak a Jarda Metelka  koordinace 
              #dvou p/person a pod tim jmen, kterym teprve (tomu poslednimu) 
              #odpovida koordinovany t-uzel   
                  continue
              if (tchild.is_member or (tchild is None and 
                                        some_coordmember_there == True) 
                                        and tparent.formeme != startswith('n:')):   
                  amrchild.modifier = ":op%d"  % opnum
                  opnum += 1    
       
class CoordRules(object):
    """This class defines rules for distinguishing various types of coordination
    at the tnode level."""

    @staticmethod
    def is_noun_attribute(tnode, tparent=None, tchildren=None):
      """Checks whether the given node is a noun attribute.
      
      Not "big and heavy ball", but yes "boy who shouted and left". 
      """
      if not tparent: # if tparent = None, condition evaluates to False.  
        tparent = tnode.parent()
      # All children must be either adj: or n:
      if not tchildren:
        tchildren = tnode.get_children()
      all_children_have_correct_formeme = True
      for tchild in tchildren:
        if tchild.formeme not in {startswith('adj:'), startswith('n:')}:
          all_children_have_correct_formeme = False
          break
          
    return (tnode.nodetype == 'coap' 
              and tparent.formeme == startswith('n:')
              and all_children_have_correct_formeme)       
            
    @staticmethod
    def is_coordinated_named_entity(amrnode):
        if  (concept in ('person', 'location') and amrnode.src_tnode = None):
            potential_tr_member_hosts = amrnode.get_descendants()
            some_coordmember_there = False
            for potential_tr_member_host in potential_tr_member_hosts:
                candidate = potential_tr_member_host.src_tnode
                if candidate.is_member == 1:
                    some_coordmember_there = True
    return some_coordmember_there                  
              
              
    