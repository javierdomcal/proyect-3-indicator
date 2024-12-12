%chk=ne10106311+Gp.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/6-311+G* gfinput fchk=all density=current iop(5/33=1) iop(4/21=100) out=wfx

ne10106311+Gp neon CASSCF(10,10) 6-311+G*

0 1
Ne 0.0 0.0 0.0

ne10106311+Gp.wfx

