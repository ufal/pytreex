   from __future__ import unicode_literals

from alex.components.nlg.tectotpl.core.block import Block
from alex.components.nlg.tectotpl.core.exception import LoadingException
from alex.components.nlg.tectotpl.tool.lexicon.cs import Lexicon

__author__ = "Silvie Cinková"
__date__ = "2015"  


class Polarity(Block):
     """
     Adds negative polarity to every negative clause (TR verb having gram/negation = neg1)
     """
     def __init__(self, scenario, args):                                               
        "Constructor, just checking the argument values"                              
        Block.__init__(self, scenario, args)                                          
        if self.language is None:                                                     
           raise LoadingException('Language must be defined!')                        
        self.lexicon = Lexicon()                                                      
                                                                                      
     def process_amrnode(self, amrnode): 
          tnode = amrnode.src_tnode                                         
      if tnode is None: 
          return
        if tnode.formeme not startswith('v:'):
          return
        if tnode.gram_negation = 'neg1':
            polaritynode = amrnode.create_child()
            polaritynode.modifier = 'polarity'
            polaritynode.concept = '-'
     
     

                 
 
       