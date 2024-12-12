%chk=neoncasscf886-31.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(8,8)/6-311++G** gfinput fchk=all density=current iop(5/33=1) out=wfx

neoncasscf886-31 neon CASSCF(8,8) 6-311++G**

0 1
Ne 0.0 0.0 0.0

neoncasscf886-31.wfx

