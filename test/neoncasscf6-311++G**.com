%chk=neoncasscf6-311++G**.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/6-311++G** gfinput fchk=all density=current iop(5/33=1) out=wfx

neoncasscf6-311++G** neon CASSCF(10,10) 6-311++G**

0 1
Ne 0.0 0.0 0.0

neoncasscf6-311++G**.wfx

