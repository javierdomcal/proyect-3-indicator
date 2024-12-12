%chk=neoncasscf8,86-31.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(8,8)/6-311++G** gfinput fchk=all density=current iop(5/33=1) out=wfx

neoncasscf8,86-31 neon CASSCF(8,8) 6-311++G**

0 1
Ne 0.0 0.0 0.0

neoncasscf8,86-31.wfx

